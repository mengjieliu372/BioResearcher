import React, { useState, useEffect } from 'react';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Chip from '@mui/material/Chip';
import { useParams } from 'react-router-dom';
import { getPapersets } from '../services/api';
import CircularProgress from '@mui/material/CircularProgress';

export default function PapersView({ query, data}) {
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
              <Typography variant='subtitle' sx={{ fontWeight: 'bold', width: '75%'}}>{paper.title}</Typography>
              {paper.flag !== undefined && (
                  <Chip
                    label={"Score: " + paper.score}
                    size="medium"
                    sx={{
                      backgroundColor: scoreData[paper.score - 1].color,
                      mx: 'auto',
                      my: 'auto',
                    }}
                  />
              )}
              <Typography sx={{ width: '10%', my: 'auto', textDecoration: 'underline'}}>
                {
                paper.flag === 3 ? "Downloaded" :
                paper.flag === 2 ? "Fail" :
                paper.flag === 1 ? "Unrelated" :
                "Unknown Status" // 如果没有匹配到，则显示默认的字符串
                }
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box>
                <Typography sx={{ fontWeight: 'bold', display: 'inline' }}>DOI:</Typography>
                <Typography sx={{ display: 'inline' }}>{paper.doi}</Typography>
              </Box>
              <Box>
                <Typography sx={{ fontWeight: 'bold' }}>Abstract:</Typography>
                <Typography sx={{ color: 'text.secondary' }}>
                  {paper.abstract}
                </Typography>
              </Box>
            </AccordionDetails>
          </Accordion>
        </Box>
      )
    });
  };

  return (
    <Box sx={{ width: '52vw'}}>
      <Typography variant="h6" sx={{color: '#108ee9'}}>
        Query:
      </Typography>
      <Typography variant="subtitle1">
        {query}
      </Typography>
      <Typography variant='h6' sx={{ mt: 1, color: '#108ee9'}}>
        Retrival Results:
      </Typography>
      <Box sx={{ display: 'flex', mb: 1, mr: 2, justifyContent: 'flex-end' }}>
        {/* score 展示 */}
        <Box sx={{ width: '25vw', height: '2vh', display: 'flex' }}>
          <Typography sx={{ display: 'flex', alignItems: 'center' }}>Evaluation Score: </Typography>
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
      </Box>
      <Box>
        {loading ? (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
              width: '52vw',
            }}
          >
            <CircularProgress />
          </Box>
        ) : (
          <Box
            sx={{
              width: '52vw',
              ml: 'auto',
              mr: 'auto',
              overflowY: 'auto',
              height: '50vh',
              maxHeight: '50vh',
              backgroundColor: '#f0f0f0',
              borderRadius: '8px',
              boxShadow: 3,
            }}
          >
            {showPapers(data)}
          </Box>
        )}
      </Box>

    </Box>
  );
}
