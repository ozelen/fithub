# FitHub 🏋️‍♂️

A comprehensive fitness and nutrition tracking API built with Django REST Framework, featuring goal management, meal tracking, and body measurements.

## 📚 Documentation

- **[🏗️ Architecture](docs/ARCHITECTURE.md)** - System design, dependencies, and data models
- **[🔌 API Reference](docs/API.md)** - Complete API documentation with examples
- **[👨‍💻 Development Guide](docs/DEVELOPMENT.md)** - Setup, workflow, and contribution guidelines
- **[🚀 Deployment](docs/DEPLOYMENT.md)** - Production deployment and CI/CD
- **[📊 ER Diagram](docs/ER_DIAGRAM.md)** - Database schema visualization
- **[🏗️ C4 Deployment](docs/C4_DEPLOYMENT.md)** - C4-style deployment architecture diagrams
- **[🔄 CI Pipeline](docs/CI_PIPELINE.md)** - Detailed CI/CD pipeline architecture and flow

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- PostgreSQL 16+
- [uv](https://astral.sh/uv) (recommended package manager)

### Installation
```bash
# Clone and setup
git clone <repository-url>
cd fithub
uv sync --extra test

# Database setup
createdb fithub
uv run manage.py migrate
uv run manage.py createsuperuser

# Start server
uv run manage.py runserver
```

**API available at:** `http://localhost:8000/`  
**Interactive docs:** `http://localhost:8000/api/docs/`

## 🛠️ Tech Stack

- **Backend**: Django 5.2.7 + Django REST Framework 3.16.1
- **Database**: PostgreSQL 16
- **Authentication**: JWT (primary) + Session + Token
- **Testing**: pytest + testcontainers + factory-boy
- **Code Quality**: black, isort, flake8, bandit, pre-commit hooks
- **Package Management**: uv
- **Deployment**: Docker + GitHub Actions CI/CD

## 🧪 Testing

```bash
make test-fast    # Quick SQLite tests
make test         # Full PostgreSQL tests
make test-ci      # CI-style tests with coverage
```

## 🔧 Development

```bash
make format       # Format code
make lint         # Check code quality
make security     # Security checks
make migrate      # Run migrations
```

## 📁 Project Structure

```
fithub/
├── docs/                      # Comprehensive documentation
├── nutrition/                 # Nutrition tracking app
├── goals/                     # Goals management app
├── authentication/            # Authentication endpoints
├── .github/workflows/         # CI/CD pipeline
├── Makefile                   # Development commands
└── pyproject.toml            # Dependencies and config
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests (`make test`)
5. Commit and push
6. Open a Pull Request

**See [Development Guide](docs/DEVELOPMENT.md) for detailed guidelines.**

## 🎯 Features

- **Nutrition Tracking**: Meals, ingredients, and nutritional data
- **Goal Management**: Fitness goals with progress tracking
- **Body Measurements**: Composition tracking over time
- **RESTful API**: Complete CRUD with filtering and pagination
- **Authentication**: JWT, session, and token authentication
- **Documentation**: Auto-generated OpenAPI/Swagger docs
- **Testing**: Comprehensive test suite with containers
- **CI/CD**: Automated testing, security, and deployment

## 🆘 Support

- **Issues**: Create an issue in the repository
- **API Docs**: `http://localhost:8000/api/docs/`
- **Documentation**: See the [docs/](docs/) directory

## 📄 License

MIT License - see LICENSE file for details.

## Open Food Facts data (`facts` app)

`facts_product` holds the global OFF catalogue trimmed to barcode, names, stores, countries, categories and
per-100g nutrients. `facts_category_nutrition` is a materialized view with median nutrients per category
(the "generic basmati rice"); `facts_category` is the OFF taxonomy (names in many languages, parents).

```bash
uv run manage.py import_openfoodfacts --taxonomy --full   # one-off: categories + full Parquet snapshot (~4.8M rows)
uv run manage.py import_openfoodfacts                      # nightly: apply the OFF daily deltas not applied yet
uv run manage.py import_openfoodfacts --file delta.json.gz # local test with one downloaded delta
```

API: `GET /api/facts/products/?q=basmati&country=en:spain`, `GET /api/facts/products/8414807516336/`,
`GET /api/facts/categories/en:basmati-rices/`. OFF rate-limits anonymous clients: `OFF_USER_AGENT` identifies us.

## Production (TrueNAS)

Push to `main`. GitHub Actions runs the tests, pushes `zelenuk/fithub:<git sha>` (and `:latest`) and POSTs
`IMAGE_TAG` to Jenkins; the `fithub-deploy` job (`Jenkinsfile`) runs `kubectl set image` on `ix-fithub`.
Secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `JENKINS_DEPLOY_URL`, `JENKINS_USER`, `JENKINS_TOKEN`.
Nightly jobs: `fithub-backup` (`Jenkinsfile.backup`, dumps to `lake/fit/backups`) and `fithub-off-import`
(`Jenkinsfile.off`, OFF deltas; run with FULL once a month). TrueNAS caches `:latest`, so deployments are pinned to the SHA.
