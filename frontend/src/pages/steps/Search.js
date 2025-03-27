import * as React from 'react';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import { Box } from '@mui/material';
import SideQuery from '../../components/SideQuery';

export default function SwitchButton() {
  const [view, setView] = React.useState('papers');

  const handleChange = (event, nextView) => {
    setView(nextView);
    if (nextView === null) {
      setView(event.currentTarget.value);
    }
  };

  const renderContent = () => {
    return <SideQuery type={view} />;
  };

  return (
    <Box>
      <Box sx={{
        display: 'flex',
        width: '70vw',
        alignItems: 'center',
        justifyContent: 'center',
        borderBottom: '1px solid #1976d2',
        height: '5vh'
      }}>
        <ToggleButtonGroup
          value={view}
          exclusive
          onChange={handleChange}
          color='primary'
        >
          <ToggleButton value="papers" aria-label="papers" sx={{ textTransform: 'none', border:'none'}}>
            Paper Source
          </ToggleButton>
          <ToggleButton value="datasets" aria-label="datasets" sx={{ textTransform: 'none', border:'none'}}>
            Dataset Source
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Box>
        {renderContent()}
      </Box>
    </Box>
  );
}
