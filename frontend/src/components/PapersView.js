import React, { useState, useEffect } from 'react';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Tooltip from '@mui/material/Tooltip';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import PriorityHighIcon from '@mui/icons-material/PriorityHigh';
import { useParams } from 'react-router-dom';
import { getPapersets } from '../services/api';
import CircularProgress from '@mui/material/CircularProgress';
import { PieChart } from '@mui/x-charts/PieChart';

export default function VerticalTabs() {
  const [paperSets, setPaperSets] = useState([]);
  const [relevanceData, setRelevanceData] = useState([]);
  const [loading, setLoading] = useState(true);
  const { id } = useParams();

  const scoreData = [
    { score: 1, color: '#FF0000' }, // 红
    { score: 2, color: '#FF8000' }, // 橙
    { score: 3, color: '#FFFF00' }, // 黄
    { score: 4, color: '#80FF00' }, // 绿
    { score: 5, color: '#00FF00' }, // 深绿
  ];

  const statusData = [
    { status: 'Downloaded', color: '#2b762f' },  // 绿
    { status: 'Failed to Download', color: '#ed6c02' }, // 橙
    { status: 'Irrelevant', color: '#d32f2f' }, // 红
  ];

  useEffect(() => {
    getPapersets(id)
      .then((res) => {
        setPaperSets(res.data); // 更新数据
        setLoading(false);
      })
      .catch((err) => {
        console.log(err);
        setLoading(false);
      });
  }, [id]);

  // 计算百分比
  let tempData = [
    { id: 0, value: 0, label: 'Irrelevant', color: '#d32f2f' },
    { id: 1, value: 0, label: 'Failed to Download', color: '#ed6c02' },
    { id: 2, value: 0, label: 'Downloaded', color: '#2b762f' },
  ]
  useEffect(() => {
    let sum = 0;
    paperSets.forEach((paper) => {
      if (paper.flag !== undefined) {
        tempData[paper.flag - 1].value += 1;
        sum += 1;
      }
    });
    tempData.forEach((item) => {
      item.value /= sum;
    });
    setRelevanceData(tempData);
  }, [paperSets]);

  const showPapers = (papers) => {
    return papers.map((paper, index) => {
      const scoreColor = scoreData.find(item => item.score === paper.score)?.color || '#FFFFFF';
      return (
        <Box>
          <Accordion key={index} sx={{ width: '100%' }}>
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              aria-controls={`panel${paper.id}-content`}
              id={`panel${paper.id}-header`}
            >
              <Typography variant='subtitle' sx={{ fontWeight: 'bold' }}>{paper.title}</Typography>
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
                    size="medium"
                  />
                </Box>
              )}
            </AccordionSummary>
            <AccordionDetails>
              <Box>
                <Typography sx={{ fontWeight: 'bold' }}>Search Query:</Typography>
                {paper.search_query}
              </Box>
              <Box>
                <Typography sx={{ fontWeight: 'bold' }}>Abstract:</Typography>
                <Typography sx={{ color: 'text.secondary' }}>
                  {paper.abstract}
                </Typography>
              </Box>
              <Box>
                <Typography sx={{ fontWeight: 'bold', display: 'inline' }}>DOI:</Typography>
                <Typography sx={{ display: 'inline' }}>{paper.doi}</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', backgroundColor: scoreColor, borderRadius: 1, pl: 1, width: 'fit-content' }}>
                <Typography sx={{ fontWeight: 'bold' }}>Score:</Typography>
                <Tooltip title="理由" arrow>
                  <Button variant="string" endIcon={<PriorityHighIcon />}>
                    {paper.score}
                  </Button>
                </Tooltip>
              </Box>
            </AccordionDetails>
          </Accordion>
        </Box>
      )
    });
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ mt: '1vh', ml: '3vw', mb: '2vh' }}>
        Retrieval Results
      </Typography>
      <Box sx={{ display: 'flex' }}>
        {/* score 展示 */}
        <Box sx={{ width: '35vw', height: '3vh', display: 'flex' }}>
          <Typography sx={{ display: 'flex', alignItems: 'center', ml: '3vw', mr: '1vw' }}>Evaluation Score: </Typography>
          {scoreData.map((item, index) => (
            <Box
              key={index}
              sx={{
                flex: 1,
                backgroundColor: item.color,
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center'
              }}
            >
              <Typography color="black">{item.score}</Typography>
            </Box>
          ))}
        </Box>
        {/* Relevance 展示 */}
        <Box sx={{ width: '35vw', height: '3vh', display: 'flex' }}>
          <Typography sx={{ display: 'flex', alignItems: 'center', ml: '3vw', mr: '1vw' }}>Relevance: </Typography>
          {statusData.map((item, index) => (
            <Box
              key={index}
              sx={{
                flex: 1,
                backgroundColor: item.color,
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
              }}
            >
              <Typography color="black">{item.status}</Typography>
            </Box>
          ))}
        </Box>
      </Box>
      <Box sx={{
        height: '62vh',
        width: '76vw',
        m: 'auto',
        mt: '2vh',
        borderRadius: '8px',
        boxShadow: 3,
      }}>
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
          <Box
            sx={{
              ml: 'auto',
              mr: 'auto',
              overflowY: 'auto',
              maxHeight: '62vh',
            }}
          >
            <Box sx={{ position: 'absolute', left: '4vw', top: '45vh' }}>
              <Typography variant='subtitle' sx={{ ml: '1vw' }}>
                Relevance Distribution:
              </Typography>
              <PieChart
                series={[{
                  data: relevanceData,
                }]}
                width={300}
                height={150}
                slotProps={{
                  legend: { hidden: true },
                }}
              />
            </Box>
            {showPapers(paperSets)}
          </Box>
        )}
      </Box>
    </Box>
  );
}
