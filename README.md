# MemoQ AIQE Connector

An AI-powered Quality Estimation (AIQE) connector for MemoQ that performs automated quality checks before the final proofreading stage.

## Features

- **Pre-Proofreading Integration**: Automatically runs quality checks before human proofreading
- **Term Base Integration**: Leverages MemoQ project term bases for terminology validation
- **MQM-Based Quality Checks**: Follows the Multidimensional Quality Metrics (MQM) framework
- **AI-Powered Analysis**: Uses advanced LLMs for sophisticated linguistic quality assessment
- **Comprehensive Error Detection**:
  - Terminology consistency
  - Grammar and syntax errors
  - Number and unit mismatches
  - Formatting issues
  - Mistranslations and meaning preservation
  - Style and tone consistency
  - Locale-specific issues

## Architecture

```
┌─────────────────┐
│  MemoQ Server   │
│  ┌───────────┐  │
│  │ Projects  │  │
│  │ Term Base │  │
│  │ Segments  │  │
│  └───────────┘  │
└────────┬────────┘
         │ REST/SOAP API
         │
┌────────▼────────────────────┐
│  AIQE Connector             │
│  ┌────────────────────────┐ │
│  │ MemoQ API Client       │ │
│  ├────────────────────────┤ │
│  │ Term Base Manager      │ │
│  ├────────────────────────┤ │
│  │ AIQE Engine            │ │
│  │  - LLM Integration     │ │
│  │  - MQM Framework       │ │
│  │  - Quality Scoring     │ │
│  ├────────────────────────┤ │
│  │ Workflow Handler       │ │
│  └────────────────────────┘ │
└─────────────────────────────┘
         │
         ▼
   Quality Reports
```

## Recommended AI Agent

**Primary Recommendation: Claude 3.5 Sonnet or GPT-4**

### Why This Choice?

1. **Multilingual Excellence**: Both models excel at understanding nuances across multiple languages
2. **Context Understanding**: Can maintain context across source and target text
3. **Structured Output**: Reliably produces MQM-formatted quality assessments
4. **Term Base Awareness**: Can be primed with terminology to check consistency
5. **Explanation Capability**: Provides detailed reasoning for detected issues

### Alternative Agents

- **GPT-4 Turbo**: Cost-effective for high-volume processing
- **Claude 3 Opus**: For maximum quality in critical projects
- **Custom Fine-tuned Models**: For specific language pairs or domains

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd AIQE

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure settings
cp config.yaml.example config.yaml
# Edit config.yaml with your MemoQ and AI provider credentials
```

## Configuration

Edit `config.yaml`:

```yaml
memoq:
  server_url: "https://your-memoq-server.com:8081"
  api_key: "your-api-key"
  username: "your-username"
  password: "your-password"

aiqe:
  ai_provider: "anthropic"  # or "openai"
  api_key: "your-ai-api-key"
  model: "claude-3-5-sonnet-20241022"  # or "gpt-4-turbo"

  # Quality thresholds
  min_confidence_score: 85
  flag_for_review_threshold: 70

mqm:
  # Enable/disable error categories
  categories:
    accuracy: true
    fluency: true
    terminology: true
    style: true
    locale_convention: true
    verity: true

workflow:
  # Integration settings
  trigger: "pre_proofreading"
  auto_approve_above: 95
  block_below: 50
```

## Usage

### Standalone Mode

Check a specific project:

```bash
python main.py --project-guid "abc-123-def-456" --mode standalone
```

### Workflow Integration Mode

Run as a service that monitors MemoQ workflow:

```bash
python main.py --mode service
```

### API Mode

Start the REST API server:

```bash
python main.py --mode api --port 8080
```

Then call via HTTP:

```bash
curl -X POST http://localhost:8080/check \
  -H "Content-Type: application/json" \
  -d '{
    "project_guid": "abc-123-def-456",
    "document_guid": "xyz-789-uvw-012"
  }'
```

## Quality Check Process

1. **Retrieve Project Data**: Fetches segments and metadata from MemoQ
2. **Load Term Bases**: Retrieves all term bases attached to the project
3. **Segment Analysis**: For each translated segment:
   - Extract source and target text
   - Load relevant terminology
   - Send to AI agent with MQM framework prompt
   - Receive structured quality assessment
4. **Error Categorization**: Classify issues by MQM categories and severity
5. **Generate Report**: Create detailed quality report with:
   - Overall quality score (0-100)
   - Error breakdown by category
   - Segment-level issues with suggestions
   - Terminology mismatches
6. **Workflow Action**: Based on score:
   - High score (>95): Auto-approve for proofreading
   - Medium score (70-95): Flag for review with notes
   - Low score (<70): Block and request revision

## MQM Error Categories

The connector follows the MQM framework with these categories:

- **Accuracy**: Mistranslations, omissions, additions
- **Fluency**: Grammar, spelling, punctuation, syntax
- **Terminology**: Inconsistent or incorrect term usage
- **Style**: Register, tone, organization
- **Locale Convention**: Date formats, currency, measurements
- **Verity**: Cultural appropriateness, legal compliance

Each error is assigned a severity:
- **Critical**: Makes content unusable or dangerous
- **Major**: Significantly impacts quality or meaning
- **Minor**: Slight quality reduction, easily understood
- **Neutral**: Style preferences without quality impact

## API Reference

### MemoQClient

```python
from src.memoq_client import MemoQClient

client = MemoQClient(server_url, username, password)
client.authenticate()

# Get project details
project = client.get_project(project_guid)

# Get segments
segments = client.get_segments(project_guid, document_guid)
```

### AIQEEngine

```python
from src.aiqe_engine import AIQEEngine

engine = AIQEEngine(ai_provider="anthropic", api_key=api_key)

# Check segment quality
result = engine.check_segment(
    source_text="Hello world",
    target_text="Hola mundo",
    source_lang="en",
    target_lang="es",
    terminology=term_base_entries
)

print(f"Quality Score: {result.quality_score}")
print(f"Issues: {result.issues}")
```

## Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run integration tests (requires MemoQ server access)
pytest tests/integration/ --integration
```

## Deployment

### Docker

```bash
docker build -t memoq-aiqe-connector .
docker run -p 8080:8080 -v $(pwd)/config.yaml:/app/config.yaml memoq-aiqe-connector
```

### Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
```

## Troubleshooting

### Authentication Errors

- Verify MemoQ credentials in config.yaml
- Ensure user has appropriate licenses (Translator Pro)
- Check HTTPS certificate validity

### AI Provider Errors

- Verify API key is valid and has credits
- Check rate limits for your provider
- Ensure model name is correct

### Performance Issues

- Adjust batch size in configuration
- Enable caching for term bases
- Consider using faster models (Claude Haiku, GPT-3.5)

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

## Support

- GitHub Issues: <repository-url>/issues
- Documentation: <repository-url>/wiki
- Email: support@example.com

## Credits

Built using:
- MemoQ Server Resources API and Web Service API
- Anthropic Claude API / OpenAI GPT API
- MQM Framework by TAUS/QTLaunchPad

## References

- [MemoQ API Documentation](https://docs.memoq.com/current/api-docs/)
- [MQM Framework](http://www.qt21.eu/mqm-definition/definition-2015-12-30.html)
- [AIQE Best Practices](https://phrase.com/phrase-quality-technologies/auto-lqa/)
