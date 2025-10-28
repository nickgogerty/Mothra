# MOTHRA GUI — Swiss Minimal Carbon Database Interface

A beautiful, data-focused graphical user interface for the MOTHRA carbon emissions database.

## Design Philosophy

This interface embodies three design philosophies:

### 1. Edward Tufte's Data Visualization Principles

- **High data-ink ratio**: Every pixel serves a purpose
- **Remove chartjunk**: No unnecessary decorations
- **Show data variation**: Focus on differences and patterns
- **Integrate graphics with text**: Labels and context flow naturally

### 2. Jacob Nielsen's Usability Heuristics

- **Visibility of system status**: Loading states, progress indicators
- **User control and freedom**: Filters, search, navigation
- **Consistency and standards**: Familiar patterns throughout
- **Error prevention**: Clear validation and helpful messages
- **Recognition over recall**: Visible options and status

### 3. Swiss Minimal Design

- **Grid-based layouts**: 8px grid system for visual rhythm
- **Typography**: Inter font for maximum legibility
- **Limited color palette**: Grayscale with minimal blue accent
- **Generous white space**: Let the data breathe
- **High contrast**: Ensure readability

## Architecture

```
MOTHRA GUI
├── Backend (FastAPI)
│   ├── RESTful API endpoints
│   ├── Database queries (PostgreSQL + pgvector)
│   ├── Semantic search integration
│   └── Statistics aggregation
│
└── Frontend (React + MUI)
    ├── Dashboard (statistics overview)
    ├── Search (semantic vector search)
    ├── Entities (browse carbon data)
    ├── Sources (monitor data sources)
    └── Swiss minimal theme
```

## Key Features

### 1. Dashboard
- **High-density overview**: Key metrics at a glance
- **Quality distribution chart**: Visualize data quality
- **Entity type breakdown**: Validation and quality by type
- **GHG scope coverage**: Scope 1/2/3 distribution
- **Minimal design**: Clean charts following Tufte principles

### 2. Semantic Search
- **Natural language queries**: Vector similarity search
- **Real-time feedback**: Instant results with similarity scores
- **Type filters**: Filter by entity type
- **Quality indicators**: Visual quality and validation status
- **Execution time**: Transparency about query performance

### 3. Entity Browser
- **Advanced filtering**: Type, validation, quality score
- **Table view**: Clean, scannable data presentation
- **Quality badges**: Color-coded quality indicators
- **Pagination**: Handle large datasets efficiently
- **Detail view**: Comprehensive entity information with emission factors

### 4. Data Sources
- **Source monitoring**: Status and health tracking
- **Crawl history**: Recent crawl logs and performance
- **Error tracking**: Visible error counts and messages
- **Priority indicators**: Critical, high, medium, low
- **Success rates**: Visual performance indicators

## Technology Stack

### Backend
- **FastAPI**: Modern, fast API framework
- **SQLAlchemy 2.0**: Async ORM
- **PostgreSQL + pgvector**: Vector similarity search
- **Pydantic**: Data validation and serialization

### Frontend
- **React 18**: Modern UI framework
- **Material-UI (MUI) 5**: Component library
- **React Router**: Client-side routing
- **TanStack Query**: Smart data fetching and caching
- **Recharts**: Data visualization
- **Vite**: Fast build tool

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with pgvector extension
- Running MOTHRA database (see main README)

### 1. Start the Backend

```bash
# Install Python dependencies (if not already done)
pip install -r requirements.txt

# Start the API server
python run_api.py

# Or use uvicorn directly
uvicorn mothra.api.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### 2. Start the Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## API Endpoints

### Search
- `POST /api/v1/search` - Semantic search with vector embeddings
- `GET /api/v1/search/suggestions` - Autocomplete suggestions

### Entities
- `GET /api/v1/entities` - List entities (paginated, filtered)
- `GET /api/v1/entities/{id}` - Get entity details
- `GET /api/v1/entity-types` - List available entity types

### Data Sources
- `GET /api/v1/sources` - List data sources (filtered)
- `GET /api/v1/sources/{id}` - Get source details with crawl history

### Statistics
- `GET /api/v1/statistics` - Comprehensive database statistics
- `GET /api/v1/statistics/summary` - Quick summary counts

## Color System

The interface uses a minimal color palette based on Swiss design:

### Primary Colors
- **Near Black** (#1a1a1a): Primary text, main actions
- **Blue** (#2563eb): Interactive elements, links
- **White** (#ffffff): Background, maximum contrast

### Semantic Colors
- **Success** (#059669): Validated data, high quality
- **Warning** (#f59e0b): Medium quality, pending
- **Error** (#dc2626): Failed operations, low quality
- **Info** (#0891b2): Informational elements

### Grayscale
- 50-900: Text hierarchy and surfaces

## Typography

### Font Family
**Inter** - A font specifically designed for legibility on screens

### Type Scale
- **H1**: 2.5rem, light (300)
- **H2**: 2rem, light (300)
- **H3**: 1.5rem, regular (400)
- **H4**: 1.25rem, medium (500)
- **Body**: 1rem, regular (400)
- **Caption**: 0.75rem, regular (400)
- **Overline**: 0.625rem, semibold (600), uppercase

## Component Library

### Key Components

1. **StatCard**: Minimal metric display
2. **QualityIndicator**: Visual quality score with progress bar
3. **StatusBadge**: Color-coded status chips
4. **EntityTable**: Filterable, sortable entity list
5. **CrawlHistory**: Timeline of source operations
6. **SearchResults**: Semantic search results with similarity

### Design Patterns

- **Cards**: 1px border, no shadow (hover shadow only)
- **Buttons**: Text-transform none, minimal padding
- **Tables**: Clean headers, subtle borders
- **Forms**: Minimal styling, clear labels
- **Charts**: Grayscale + semantic colors only

## Data Visualization

Following Tufte's principles:

1. **No chartjunk**: Remove unnecessary gridlines, decorations
2. **Data-ink ratio**: Maximize information, minimize decoration
3. **Small multiples**: Compare data side-by-side
4. **Clear labels**: Integrate text with graphics
5. **Show causality**: Explain what the data means

### Chart Types Used
- **Bar charts**: Quality distribution, entity breakdowns
- **Linear progress**: Quality scores, success rates
- **Tables**: Detailed data with sorting

## Performance

### Optimization Strategies
- **React Query caching**: 5-minute stale time
- **Pagination**: Handle large datasets efficiently
- **Lazy loading**: Load data on demand
- **Debounced search**: Reduce API calls
- **Optimistic updates**: Immediate UI feedback

### Lighthouse Scores (Target)
- Performance: 90+
- Accessibility: 95+
- Best Practices: 90+
- SEO: 90+

## Responsive Design

### Breakpoints
- **xs**: 0px (mobile)
- **sm**: 600px (small tablets)
- **md**: 900px (tablets)
- **lg**: 1200px (desktops)
- **xl**: 1536px (large desktops)

### Mobile Considerations
- Collapsible sidebar navigation
- Stacked layouts for small screens
- Touch-friendly targets (48x48px minimum)
- Readable typography at all sizes

## Accessibility

- **WCAG 2.1 AA compliant**
- **Keyboard navigation**: Tab through all interactive elements
- **ARIA labels**: Screen reader support
- **Color contrast**: 4.5:1 minimum for text
- **Focus indicators**: Clear visual focus states
- **Alt text**: All images and icons

## Development Guidelines

### Code Style
- Functional components with hooks
- MUI's `sx` prop for styling
- Keep components under 300 lines
- Extract reusable logic to custom hooks
- Comment complex algorithms

### File Organization
```
src/
├── api/          # API client and endpoints
├── components/   # Reusable components
├── pages/        # Page-level components
├── theme.js      # Theme configuration
├── App.jsx       # App root
└── main.jsx      # Entry point
```

### Naming Conventions
- **Components**: PascalCase (EntityDetail.jsx)
- **Functions**: camelCase (getEntity)
- **Constants**: UPPER_SNAKE_CASE (API_BASE_URL)
- **Files**: Match component names

## Testing

### Recommended Testing Strategy
1. **Unit tests**: Component logic with Vitest
2. **Integration tests**: API interactions with MSW
3. **E2E tests**: User flows with Playwright
4. **Visual regression**: Screenshot diffs with Percy

## Deployment

### Production Build
```bash
# Backend
uvicorn mothra.api.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run build
# Serve the dist/ folder with nginx or similar
```

### Environment Variables

**Backend** (.env):
```
DATABASE_URL=postgresql://user:pass@localhost:5432/mothra
```

**Frontend** (.env):
```
VITE_API_URL=https://api.mothra.example.com/api/v1
```

## Future Enhancements

### Potential Features
- [ ] Dark mode toggle
- [ ] Export data to CSV/JSON
- [ ] Advanced query builder
- [ ] Custom dashboards
- [ ] Real-time updates via WebSocket
- [ ] Comparison view (compare entities side-by-side)
- [ ] Batch operations
- [ ] User preferences and saved searches
- [ ] Data import wizard
- [ ] Notification system

### Performance
- [ ] Service worker for offline support
- [ ] Code splitting by route
- [ ] Image optimization
- [ ] Bundle size optimization

## Troubleshooting

### Common Issues

**API connection failed**
- Ensure backend is running on port 8000
- Check CORS settings in FastAPI
- Verify DATABASE_URL is correct

**Slow search performance**
- Check PostgreSQL indexes are created
- Ensure pgvector extension is installed
- Monitor database query performance

**Build errors**
- Clear node_modules and reinstall
- Check Node.js version (18+)
- Verify all dependencies are installed

## Contributing

Follow the design principles:
1. **Tufte**: High data-ink ratio, no chartjunk
2. **Nielsen**: Usability first, clear feedback
3. **Swiss**: Minimal, grid-based, high contrast

## Resources

### Design Inspiration
- Edward Tufte: *The Visual Display of Quantitative Information*
- Jacob Nielsen: *Usability Heuristics*
- Swiss Design: Josef Müller-Brockmann
- Material Design: Google's design system
- Inter Font: https://rsms.me/inter/

### Technical Documentation
- React: https://react.dev
- Material-UI: https://mui.com
- FastAPI: https://fastapi.tiangolo.com
- TanStack Query: https://tanstack.com/query

## License

Part of the MOTHRA project.

---

**Built with care for data clarity and user experience.**
