import React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TestData from '../utils/PapersetProcess';

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
  const queriesData = TestData;


  const showPapers = (papers) => {
    return (
      papers.map((paper) => (
        <Accordion key={paper.id}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls={`panel${paper.id}-content`}
            id={`panel${paper.id}-header`}
          >
            {paper.title}
          </AccordionSummary>
          <AccordionDetails>
            <Typography>Abstract:{paper.abstract}</Typography>
            <Typography>DOI:{paper.doi}</Typography>
            <Typography>Score:{paper.score}</Typography>
          </AccordionDetails>
        </Accordion>
      ))
    );
  };

  const [value, setValue] = React.useState(0);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  return (
    <Box
      sx={{
        display: 'flex',
        height: '78vh',
        backgroundColor: '#ffffff',
        borderRadius: '8px',
      }}
    >

      {/* 左侧标签栏 */}
      <Box
        sx={{
          height: '78vh'
        }}>
        <Tabs
          orientation="vertical"
          variant="scrollable"
          value={value}
          onChange={handleChange}
          aria-label="Vertical tabs"
          sx={{ borderRight: 1, 
                borderColor: 'divider',
                width: '8vw'
              }}
        >
          {queriesData.map((query, index) => (
            <Tab label={query.query} {...a11yProps(index)} key={index} />
          ))}
        </Tabs>
      </Box>

      {/* 右侧内容 */}
      <Box
        sx={{
          height: '78vh',
          backgroundColor: '#f0f0f0',
        }}
      >
        {queriesData.map((query, index) => (
          <TabPanel value={value} index={index} key={index}>
            <Box
              sx={{
                ml: 'auto',
                mr: 'auto',
                overflowY: 'auto',
                maxHeight: '72vh',
              }}
            >
              {showPapers(query.papers)}
            </Box>
          </TabPanel>
        ))}
      </Box>
    </Box>
  );
}
