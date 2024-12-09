import * as React from 'react';
import ReportSection from "../../components/ReportSection";
import report1 from "../../data/experiment_program1.json";
import report2 from "../../data/experiment_program2.json";
import report3 from "../../data/experiment_program3.json";
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';

export function Report1() {
    const data = report1

    return (
        <div style={{ padding: '20px' }}>
            {Object.entries(data).map(([partKey, partValue]) => {
                const steps = Object.entries(partValue)
                    .filter(([key]) => key.startsWith('step')) // 过滤出步骤数据
                    .map(([key, value]) => ({
                        title: `Step ${key.split(' ')[1]}`,  // Step 1, Step 2
                        details: value['implementation details'],
                        references: value['Reference Source'],
                    }));

                return (
                    <ReportSection key={partKey} part={partValue['Part 1']} steps={steps} />
                );
            })}
        </div>
    );
}



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

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={value} onChange={handleChange} aria-label="basic tabs example">
          <Tab label="Experimental Protocol 1" {...a11yProps(0)} />
          <Tab label="Experimental Protocol 2" {...a11yProps(1)} />
          <Tab label="Experimental Protocol 3" {...a11yProps(2)} />
        </Tabs>
      </Box>
      <CustomTabPanel value={value} index={0}>
        {Report1()}
      </CustomTabPanel>
      <CustomTabPanel value={value} index={1}>
        Item Two
      </CustomTabPanel>
      <CustomTabPanel value={value} index={2}>
        Item Three
      </CustomTabPanel>
    </Box>
  );
}
