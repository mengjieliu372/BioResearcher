import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import ExpDesignContent from '../../components/ExpDesignContent';
import { useParams } from 'react-router-dom';
import { getExpDesign } from '../../services/api';
import ErrorPage from '../../components/ErrorPage';

function CustomTabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

CustomTabPanel.propTypes = {
  children: PropTypes.node,
  index: PropTypes.number.isRequired,
  value: PropTypes.number.isRequired,
};

function a11yProps(index) {
  return {
    id: `simple-tab-${index}`,
    'aria-controls': `simple-tabpanel-${index}`,
  };
}




export default function ExperimentalDesign() {
  const [value, setValue] = React.useState(0);
  const [content, setContent] = React.useState(null);
  const { id } = useParams();

  React.useEffect(() => {
    getExpDesign(id, value)
      .then((res) => {
        setContent(<ExpDesignContent data={res.data} />);
      })
      .catch((err) => {
        setContent(<ErrorPage code={err.status} message={err.response.data.detail} />);
      });
  }, [value]);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  
  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={value} onChange={handleChange} aria-label="basic tabs example" centered>
          <Tab label="Experimental Protocol 1" sx={{ textTransform: 'none' }} {...a11yProps(0)} />
          <Tab label="Experimental Protocol 2" sx={{ textTransform: 'none' }} {...a11yProps(1)} />
          <Tab label="Experimental Protocol 3" sx={{ textTransform: 'none' }} {...a11yProps(2)} />
        </Tabs>
      </Box>

      <Box
        sx={{
          height: '70vh',
          maxHeight: '70vh',
          overflowY: 'auto',
          width: '65vw',
          ml: 'auto',
          mr: 'auto',
          mt: '1vh',
          borderRadius: '8px',
          boxShadow: 3,
        }}
      >

        <CustomTabPanel value={value} index={0}>
          {content}
        </CustomTabPanel>
        <CustomTabPanel value={value} index={1}>
          {content}
        </CustomTabPanel>
        <CustomTabPanel value={value} index={2}>
          {content}
        </CustomTabPanel>
      </Box>
    </Box>
  );
}
