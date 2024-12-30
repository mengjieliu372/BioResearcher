import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Tooltip from '@mui/material/Tooltip';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import ErrorIcon from '@mui/icons-material/Error';
import { useParams } from 'react-router-dom';
import { getPapersets } from '../services/api';
import CircularProgress from '@mui/material/CircularProgress';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <Box
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
    </Box>
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
    getPapersets(id)
      .then((res) => {
        setQueriesData(res.data); // 更新数据
        setLoading(false);
      })
      .catch((err) => {
        console.log(err);
        setLoading(false);
      });
  }, [id]);

  const showPapers = (papers) => {
    return papers.map((paper, index) => (
      <Accordion key={index} sx={{ width: '100%' }}>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls={`panel${paper.id}-content`}
          id={`panel${paper.id}-header`}
        >
          <Typography sx={{ fontWeight: 'bold' }}>{paper.title}</Typography>
          {paper.flag !== undefined && (
            <Box sx={{ ml: 'auto' }}>
              <Chip
                label={
                  paper.flag === 3
                    ? 'Downloaded'
                    : paper.flag === 2
                    ? 'Failed to Download'
                    : 'Irrelevant'
                }
                color={
                  paper.flag === 3
                    ? 'success'
                    : paper.flag === 2
                    ? 'warning'
                    : 'error'
                }
                size="small"
              />
            </Box>
          )}
        </AccordionSummary>
        <AccordionDetails>
          <Typography>
            <Typography sx={{ fontWeight: 'bold' }}>Abstract:</Typography>
            {paper.abstract}
          </Typography>
          <Typography>
            <Typography sx={{ fontWeight: 'bold' }}>DOI:</Typography>
            {paper.doi}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography sx={{ fontWeight: 'bold' }}>Score:</Typography>
            <Tooltip title="理由" arrow>
              <Button variant="string" endIcon={<ErrorIcon />}>
                {paper.score}
              </Button>
            </Tooltip>
          </Box>
        </AccordionDetails>
      </Accordion>
    ));
  };

  const [value, setValue] = useState(0);

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
      <Box sx={{ height: '78vh' }}>
        <Tabs
          orientation="vertical"
          variant="scrollable"
          value={value}
          onChange={handleChange}
          aria-label="Vertical tabs"
          sx={{
            borderRight: 1,
            borderColor: 'divider',
            width: '8vw',
          }}
        >
          {queriesData.length > 0 && queriesData.map((query, index) => (
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
        {/* 如果正在加载数据，则显示 CircularProgress */}
        {loading ? (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
            }}
          >
            <CircularProgress />
          </Box>
        ) : (
          // 数据加载完成，显示查询内容
          queriesData.length > 0 && queriesData.map((query, index) => (
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
          ))
        )}
      </Box>
    </Box>
  );
}
