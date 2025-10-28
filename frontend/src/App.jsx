/**
 * MOTHRA Main Application
 * Swiss minimal design with clear navigation hierarchy
 */

import { Routes, Route } from 'react-router-dom'
import { Box } from '@mui/material'

// Layout
import AppLayout from './components/Layout/AppLayout'

// Pages
import Dashboard from './pages/Dashboard'
import Search from './pages/Search'
import Entities from './pages/Entities'
import EntityDetail from './pages/EntityDetail'
import Sources from './pages/Sources'
import SourceDetail from './pages/SourceDetail'

function App() {
  return (
    <AppLayout>
      <Box sx={{ minHeight: 'calc(100vh - 128px)' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/search" element={<Search />} />
          <Route path="/entities" element={<Entities />} />
          <Route path="/entities/:id" element={<EntityDetail />} />
          <Route path="/sources" element={<Sources />} />
          <Route path="/sources/:id" element={<SourceDetail />} />
        </Routes>
      </Box>
    </AppLayout>
  )
}

export default App
