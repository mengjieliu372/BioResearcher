import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import LieratureProcessingContent from '../../components/LiteratureProcessingContent';
import { getPaperInfo } from '../../services/api';
import { getReportAnalysis } from '../../services/api';
import { useParams } from 'react-router-dom';
import ErrorPage from '../../components/ErrorPage';

function TabPanel(props) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`vertical-tabpanel-${index}`}
      aria-labelledby={`vertical-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          <Typography>{children}</Typography>
        </Box>
      )}
    </div>
  );
}

TabPanel.propTypes = {
  children: PropTypes.node,
  index: PropTypes.number.isRequired,
  value: PropTypes.number.isRequired,
};

function a11yProps(index) {
  return {
    id: `vertical-tab-${index}`,
    'aria-controls': `vertical-tabpanel-${index}`,
  };
}



export default function VerticalTabs() {
  const { id } = useParams();
  const [value, setValue] = React.useState(0);
  const [content, setContent] = React.useState(null);
  const [paperInfo, setPaperInfo] = React.useState([]);

  React.useEffect(() => {
    getPaperInfo(id)
      .then((res) => {
        setPaperInfo(res.data);
      })
      .catch((err) => {
        // setContent(<ErrorPage code={err.status} message={err.response.data.message} />);
      });
  }, [id]);

  React.useEffect(() => {
    getReportAnalysis(id, value)
      .then((res) => {
        const { title, data } = res.data;
        setContent(<LieratureProcessingContent data={data} paper_title={title}/>);
      })
      .catch((err) => {
        console.log(err);
      });
  }, [value]);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  return (
    <Box
      sx={{ flexGrow: 1, display: 'flex', height: '78vh'}}
    >
      <Tabs
        orientation="vertical"
        variant="scrollable"
        value={value}
        onChange={handleChange}
        aria-label="Vertical tabs example"
        sx={{ borderRight: 1, borderColor: 'divider' }}
      >
        {paperInfo.map((paper, index) => {
          return <Tab
            key={index}
            label={`Related Paper ${index + 1}`}
            {...a11yProps(index)}
            sx={{
              textTransform: 'none',
              width: '9.5vw',
            }} />
        })}
      </Tabs>

      <Box
        sx={{
          height: '78vh',
          width: '60vw'
        }}
      >
        {paperInfo.map((paper, index) => {
          return (
            <Box
              key={index}
              sx={{
                ml: 'auto',
                mr: 'auto',
                overflowY: 'auto',
                maxHeight: '72vh',
              }}
            >
              <TabPanel value={value} index={index}>
                {content}
              </TabPanel>
            </Box>
          )
        })}
      </Box>
    </Box>
  );
}
