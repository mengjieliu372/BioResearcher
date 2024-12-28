import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import { GetReport } from "../../utils/ReportProcess";
import { GetAnalysis } from '../../utils/ReportProcess';
import { GetPaperInfo } from '../../utils/ReportProcess';
import LieratureProcessingContent from '../../components/LiteratureProcessingContent';

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
  const paper_info = GetPaperInfo();

  const [value, setValue] = React.useState(0);

  const [content, setContent] = React.useState(null);
  React.useEffect(() => {
    // 根据 value 从 report 中选择数据
    let report = GetReport(value);
    let analysis = GetAnalysis(value);
    setContent(<LieratureProcessingContent report={report} analysis={analysis} />);
  }, [value]);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  return (
    <Box
      sx={{ flexGrow: 1, bgcolor: 'background.paper', display: 'flex', height: '78vh' }}
    >
      <Tabs
        orientation="vertical"
        variant="scrollable"
        value={value}
        onChange={handleChange}
        aria-label="Vertical tabs example"
        sx={{ borderRight: 1, borderColor: 'divider' }}
      >
        {paper_info.map((paper, index) => {
          return <Tab
            key={index}
            label={paper.title}
            {...a11yProps(index)}
            sx={{
              textTransform: 'none',
              height: '12vh',
            }} />
        })}
      </Tabs>

      <Box
        sx={{
          height: '78vh',
          width: '77vw',
          backgroundColor: '#e3fdff',
        }}
      >
        {paper_info.map((paper, index) => {
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
