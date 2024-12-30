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
import Chip from '@mui/material/Chip';
import { getDatasets } from '../services/api';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

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
  const [queriesData, setQueriesData] = useState([]);
  const [loading, setLoading] = useState(true);
  const { id } = useParams();

  useEffect(() => {
    getDatasets(id)
      .then((res) => {
        setQueriesData(res.data); // 更新数据
        setLoading(false);
      })
      .catch((err) => {
        console.log(err);
        setLoading(false);
      });
  }, [id]);

  const showDatasets = (datasets) => {
    return (
      Object.entries(datasets).map(([key, value]) => (
        <Accordion 
          key={key}
          sx={{
            width: '100%',
          }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls={`panel${key}-content`}
            id={`panel${key}-header`}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
              <Typography sx={{ flexGrow: 1 }}>{value.Title}</Typography>
              {value.isRelated !== undefined && (
                <Chip
                  label={value.isRelated ? 'Relevant' : 'Irrelevant'}
                  color={value.isRelated ? 'success' : 'error'}
                  size="small"
                  sx={{ ml: 2 }}
                />
              )}
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography>Identifier : {key}</Typography>
            <Typography>Status: {value.Status}</Typography>
            <Typography>Summary: {value.Summary}</Typography>
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
        flexDirection: 'row',
        height: '78vh',
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
          sx={{
            borderRight: 1,
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
          width: '77vw',
          backgroundColor: '#e3fdff',
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
              {showDatasets(query.datasets)}
            </Box>
          </TabPanel>
        ))}
      </Box>
    </Box>
  );
}
