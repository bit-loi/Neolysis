# Neolysis

AI-powered drug discovery platform for ASEAN neglected tropical disease (NTD) research.

## Overview

Neolysis is an open-access, browser-based platform designed to accelerate early-stage drug discovery for neglected tropical diseases prevalent in ASEAN regions. The platform provides researchers with interactive 3D protein visualization, pre-computed molecular docking scores, and AI-generated research insights.

## Target Diseases

- Leptospirosis
- Scrub Typhus
- Melioidosis
- Dengue

## Features

### 3D Protein Visualization
- Interactive protein structure viewer powered by 3Dmol.js
- Multiple rendering styles: cartoon, stick, and surface
- Fetched directly from RCSB PDB database
- AlphaFold DB integration for predicted structures

### Drug Candidate Analysis
- Pre-computed docking scores via AutoDock Vina
- Lipinski Rule of Five compliance checking
- Veber rules for oral bioavailability assessment
- Molecular property calculations (MW, LogP, TPSA, etc.)

### AI Research Insights
- Contextual narratives generated for each compound-target pair
- Disease relevance and ASEAN burden analysis
- Research gap identification and next-step recommendations

### Open Access
- All data freely accessible without registration
- No licensing requirements
- Built on public databases: AlphaFold DB, RCSB PDB, PubChem

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **3D Viewer**: 3Dmol.js (CDN)
- **Icons**: Lucide React

## Project Structure

```
app/
├── page.tsx                  # Landing page
├── layout.tsx                # Root layout with navigation
├── targets/
│   ├── page.tsx              # Target explorer grid
│   └── [id]/page.tsx        # Protein detail page
├── compound/[id]/page.tsx    # Compound detail page
├── about/page.tsx            # About page
├── methodology/page.tsx      # Methodology documentation
└── api/insight/route.ts     # AI insight API endpoint

components/
├── layout/                   # Navbar, Footer
├── landing/                  # Landing page sections
├── targets/                  # Target cards and grid
├── explorer/                 # Protein viewer and compound list
├── compound/                 # Compound detail components
└── ui/                      # Reusable UI components

lib/
├── types.ts                  # TypeScript interfaces
├── targets.ts                # Protein target data
├── docking.ts                # Docking score and compound data
└── utils.ts                 # Utility functions
```

## Getting Started

### Prerequisites

- Node.js 20 or later
- npm, yarn, pnpm, or bun

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd neolysis-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Environment Variables

Not required for development. For production deployment, configure:

- `NEXT_PUBLIC_API_URL` - Backend API endpoint (if connecting to external services)

## API Endpoints

### GET /api/insight

Returns AI-generated research insights for a compound-target pair.

**Request Body:**
```json
{
  "targetId": "lipl32",
  "compoundCid": "23667740"
}
```

**Response:**
```json
{
  "targetId": "lipl32",
  "compoundCid": "23667740",
  "whyTargetMatters": "...",
  "whyCompoundPromising": "...",
  "researchGap": "...",
  "generatedAt": "2025-01-15T00:00:00Z"
}
```

## Data Sources

| Source | Description |
|--------|-------------|
| [AlphaFold DB](https://alphafold.ebi.ac.uk) | AI-predicted protein structures |
| [RCSB PDB](https://www.rcsb.org) | Experimental protein structures |
| [PubChem](https://pubchem.ncbi.nlm.nih.gov) | Chemical compound database |
| [AutoDock Vina](https://vina.scripps.edu) | Molecular docking software |

## Methodology

Molecular docking scores are computed using AutoDock Vina with the following parameters:

- Exhaustiveness: 32
- Number of binding modes: 10
- Binding site coordinates derived from PDB structures

See [/methodology](/methodology) for detailed documentation.

## Disclaimer

This platform is designed for research exploration and hypothesis generation only. AI-generated insights and computational predictions should not be interpreted as clinical recommendations. All findings require experimental validation through appropriate laboratory methods.

## Contributing

Contributions are welcome. Please ensure code passes linting and type checking before submitting pull requests.

```bash
npm run lint
```

## License

Open-access. All data sourced from public databases with appropriate attribution.

## Acknowledgments

- AlphaFold team at DeepMind
- RCSB PDB consortium
- PubChem/National Center for Biotechnology Information
- The Scripps Research Institute for AutoDock Vina
