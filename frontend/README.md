# MOTHRA Frontend

A beautiful, Swiss-minimal GUI for the MOTHRA carbon emissions database.

## Design Philosophy

This interface follows three key design principles:

1. **Edward Tufte's Data Visualization Principles**
   - High data-ink ratio
   - Remove chartjunk
   - Show data variation
   - Clear integration of graphics with text

2. **Jacob Nielsen's Usability Heuristics**
   - Visibility of system status
   - User control and freedom
   - Consistency and standards
   - Error prevention and recovery

3. **Swiss Minimal Design**
   - Grid-based layouts
   - Sans-serif typography (Inter)
   - Limited color palette
   - Generous white space
   - High contrast for readability

## Features

- **Semantic Search**: Natural language search with vector embeddings
- **Entity Browser**: Filter and explore carbon entities
- **Data Visualizations**: Clean, Tufte-inspired charts and graphs
- **Source Monitoring**: Track data source health and crawl history
- **Quality Indicators**: Visual feedback on data quality and validation
- **Responsive Design**: Works on desktop, tablet, and mobile

## Tech Stack

- **React 18** - UI framework
- **Material-UI (MUI) 5** - Component library
- **React Router** - Navigation
- **TanStack Query** - Data fetching and caching
- **Recharts** - Data visualization
- **Axios** - HTTP client
- **Vite** - Build tool

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

The app will be available at http://localhost:3000

### Building for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and endpoints
│   ├── components/       # Reusable components
│   │   └── Layout/      # Layout components
│   ├── pages/           # Page components
│   │   ├── Dashboard.jsx      # Overview with statistics
│   │   ├── Search.jsx         # Semantic search interface
│   │   ├── Entities.jsx       # Entity list with filters
│   │   ├── EntityDetail.jsx   # Entity detail view
│   │   ├── Sources.jsx        # Data sources list
│   │   └── SourceDetail.jsx   # Source monitoring
│   ├── theme.js         # Swiss minimal theme
│   ├── App.jsx          # Main app component
│   └── main.jsx         # App entry point
├── index.html           # HTML template
├── vite.config.js       # Vite configuration
└── package.json         # Dependencies
```

## API Integration

The frontend connects to the MOTHRA FastAPI backend. Endpoints:

- `POST /api/v1/search` - Semantic search
- `GET /api/v1/entities` - List entities
- `GET /api/v1/entities/{id}` - Entity details
- `GET /api/v1/sources` - List data sources
- `GET /api/v1/sources/{id}` - Source details
- `GET /api/v1/statistics` - Database statistics

## Typography

The interface uses **Inter** font family for its excellent readability and Swiss design heritage.

## Color Palette

- **Primary**: Near-black (#1a1a1a) - Main text and actions
- **Secondary**: Blue (#2563eb) - Interactive elements
- **Background**: White (#ffffff) - Maximum contrast
- **Surface**: Light gray (#fafafa) - Card backgrounds
- **Text**: Gray scale - Clear hierarchy

## Development

### Code Style

- Use functional components with hooks
- Follow Material-UI's sx prop for styling
- Keep components focused and reusable
- Comment complex logic

### Performance

- React Query handles caching and background updates
- Lazy loading for routes (can be added)
- Optimized re-renders with proper memoization
- Efficient data structures

## License

Part of the MOTHRA project.
