import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';


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



function RenderContent(data) {
  return (
    <Container>
      {Object.entries(data).map(([part, steps]) => (
        <Accordion key={part}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="panel1a-content"
            id="panel1a-header"
          >
            {part + ": " + steps[part]}
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
                    <Box>
                      <strong>Implementation Details:</strong>
                      {details["implementation details"]
                        .split('\n')
                        .map((line, index) => (
                          <Box key={index}>{line}</Box>
                        ))}
                    </Box>
                    <Box mt={2}>
                      <strong>Reference Source:</strong>
                      {Object.entries(details["Reference Source"]).map(
                        ([source, parts]) => (
                          <Box key={source}>
                            {Object.entries(parts).map(([part, steps]) => (
                              <Box key={part}>
                                {steps.map(stepKey => (
                                  <Box key={stepKey}>
                                    {`${source}: ${part} ${stepKey}`}
                                  </Box>
                                ))}
                              </Box>
                            ))}
                          </Box>
                        )
                      )}
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))}
          </AccordionDetails>
        </Accordion>
      ))}
    </Container>
  );
}


export default function ExperimentalDesign() {
  const [value, setValue] = React.useState(0);
  const [content, setContent] = React.useState(null);

  React.useEffect(() => {
    const prog = "experiment_program" + (value + 1);
    console.log(prog);
    import(`../../data/${prog}.json`)
      .then(data => {
        setContent(RenderContent(data.default));
      })
      .catch(err => console.error(err));
  }, [value]); // 仅当 value 变化时触发
  
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
