import * as React from 'react';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import { Box } from '@mui/material';
import PapersView from '../../components/PapersView';
import DatasetsView from '../../components/DatasetsView';

export default function SwitchButton() {
  const [view, setView] = React.useState('papers');

  const handleChange = (event, nextView) => {
    setView(nextView);
    if (nextView === null) {
      setView(event.currentTarget.value);
    }
  };

  const renderContent = () => {
    switch (view) {
      case 'papers':
        return <PapersView />;
      case 'datasets':
        return <DatasetsView />;
      default:
        return null;
    }
  };

  return (
    <Box sx={{
      display: 'flex',
      flexDirection: 'row',
    }}>
      <Box sx={{
        display: 'flex',
        flexDirection: 'column',
        width: '5vw'
      }}>
        <ToggleButtonGroup
          orientation="vertical"
          value={view}
          exclusive
          onChange={handleChange}
          color='primary'
        >
          <ToggleButton value="papers" aria-label="papers">
            Papers
          </ToggleButton>
          <ToggleButton value="datasets" aria-label="datasets">
            Datasets
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Box
        sx={{
          width: '85vw',
        }}
      >
        {renderContent()}
      </Box>
    </Box>
  );
}
