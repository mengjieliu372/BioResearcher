import * as React from 'react';
import ReportSection from "../../components/ReportSection";
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Typography from '@mui/material/Typography';
import {GetReport} from "../../utils/ReportProcess";
import { GetAnalysis } from '../../utils/ReportProcess';


let report1=GetReport(0);
let analysis1=GetAnalysis(0);

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
  
  
  export default function LiteratureProcessing() {
    const [value, setValue] = React.useState(0);
    const [content, setContent] = React.useState(null);
    

    React.useEffect(() => {
        // 根据 value 从 report 中选择数据
        report1=GetReport(value);
        analysis1=GetAnalysis(value);
        setContent(RenderContent(report1,analysis1));
      }, [value]);
    
    const handleChange = (event, newValue) => {
      setValue(newValue);
    };
    
    
    
    return (
      <Box sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={value} onChange={handleChange} aria-label="basic tabs example" centered>
            <Tab label="Paper 1" sx={{ textTransform: 'none' }} {...a11yProps(0)} />
            <Tab label="Paper 2" sx={{ textTransform: 'none' }} {...a11yProps(1)} />
            <Tab label="Paper 3" sx={{ textTransform: 'none' }} {...a11yProps(2)} />
          </Tabs>
        </Box>
  
        <Box
          sx={{
            height: '72vh',
            maxHeight: '70vh',
            overflowY: 'auto',
            backgroundColor: '#f5f5f5',
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
