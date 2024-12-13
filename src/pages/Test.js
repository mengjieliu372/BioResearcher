import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { GetReport } from "../utils/ReportProcess";
import { GetAnalysis } from '../utils/ReportProcess';
import { GetPaperInfo } from '../utils/ReportProcess';

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


function RenderContent(data,data2) {
    

  return (
      <Container>
          {Object.entries(data).map(([part, steps]) => (
              <Accordion key={part}>
                  <AccordionSummary
                      expandIcon={<ExpandMoreIcon />}
                      aria-controls="panel1a-content"
                      id="panel1a-header"
                  >

                      {part + ": " +steps[part]}

                      {<Box sx={{ backgroundColor: 'green', padding: 1 }}>
                      <Typography variant="body1" color="white">
                       <div>Referability:</div>
                       {data2[part]["Referability"]}
                      </Typography>
                      </Box>}

                       <Accordion >
                          <AccordionSummary 
                          expandIcon={<ExpandMoreIcon />}
                          aria-controls="panel1a-content"
                          id="panel1a-header">
                          {<h5>Reason</h5>}
                          </AccordionSummary>
                          <AccordionDetails>
                          {data2[part]["Reason"]}
                          </AccordionDetails>

                      </Accordion>

                      <Accordion >
                          <AccordionSummary
                          expandIcon={<ExpandMoreIcon />}
                          aria-controls="panel1a-content"
                          id="panel1a-header">
                          {<h5>Suggestions</h5>}
                          </AccordionSummary>
                          <AccordionDetails>
                          {data2[part]["Suggestions"]}
                          </AccordionDetails>
                          
                      </Accordion>
                  </AccordionSummary>
                  <AccordionDetails>
                      {Object.entries(steps)
                        .slice(1)
                        .map(([step, details]) => (
                          <Accordion key={step}>
                              <AccordionSummary
                                  expandIcon={<ExpandMoreIcon />}
                                  aria-controls="panel1a-content"
                                  id="panel1a-header"
                              >
                                  {step}
                              </AccordionSummary>
                              <AccordionDetails>
                                <div>{<h2>Implementation Details: </h2>} </div>
                                {details["implementation details"]}
                                <div>
                                {<h2>"Original text:"</h2>}{details["original text"]}
                                </div>
                                <div>
                                {<h2>"Results:"</h2>}{details["results"]}
                                </div>
                                <div>
                                {<h2>"Results original text:"</h2>}{details["results original text"]}
                                </div>
                                </AccordionDetails>
                          </Accordion>
                      ))}
                  </AccordionDetails>
              </Accordion>
          ))}
      </Container>
  );
}


export default function VerticalTabs() {
  const paper_info = GetPaperInfo();

  const [value, setValue] = React.useState(0);

  const [content, setContent] = React.useState(null);
  
  React.useEffect(() => {
    // 根据 value 从 report 中选择数据
    let report = GetReport(value);
    let analysis = GetAnalysis(value);
    setContent(RenderContent(report, analysis));
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
            label={paper.title} 
            {...a11yProps(index)} 
            sx={{ 
              textTransform: 'none',
              height: '10vh',
            }} />
        })}
      </Tabs>
      <Box>
        {paper_info.map((paper, index) => {
          return (
            <TabPanel value={value} index={index}>
              {content}
            </TabPanel>
          )
        })}
      </Box>
    </Box>
  );
}
