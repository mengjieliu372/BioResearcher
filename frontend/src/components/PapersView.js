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
import ErrorIcon from '@mui/icons-material/Error';
import { useParams } from 'react-router-dom';
import { getPapersets } from '../services/api';
import CircularProgress from '@mui/material/CircularProgress';


export default function VerticalTabs() {
  const [paperSets, setPaperSets] = useState([]);
  const [loading, setLoading] = useState(true);
  const { id } = useParams();

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
          <Box>
            <Typography sx={{ fontWeight: 'bold' }}>Search Query:</Typography>
            {paper.search_query}
          </Box>
          <Box>
            <Typography sx={{ fontWeight: 'bold' }}>Abstract:</Typography>
            {paper.abstract}
          </Box>
          <Box>
            <Typography sx={{ fontWeight: 'bold' }}>DOI:</Typography>
            {paper.doi}
          </Box>
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

  return (
    <Box sx={{
      height: '72vh',
      width: '76vw',
      m: 'auto',
      mt: '3vh',
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
            maxHeight: '72vh',
          }}
        >
          {showPapers(paperSets)}
        </Box>
      )}
    </Box>
  );
}
