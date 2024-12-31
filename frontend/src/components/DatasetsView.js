import React from 'react';
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
import CircularProgress from '@mui/material/CircularProgress';

export default function VerticalTabs() {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const { id } = useParams();

  useEffect(() => {
    getDatasets(id)
      .then((res) => {
        setDatasets(res.data); // 更新数据
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
            <Box>
              <Typography sx={{ fontWeight: 'bold' }}>Search Query : </Typography>
              {value.search_query}
            </Box>
            <Box>
              <Typography sx={{ fontWeight: 'bold' }}>Identifier:</Typography>
              {key}
            </Box>
            <Box>
              <Typography sx={{ fontWeight: 'bold' }}>Status:</Typography>
              {value.Status}
            </Box>
            <Box>
              <Typography sx={{ fontWeight: 'bold' }}>Summary:</Typography>
              {value.Summary}
            </Box>
          </AccordionDetails>
        </Accordion>
      ))
    );
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
      {
        loading ? (
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
          {showDatasets(datasets)}
        </Box>
        )
      }
    </Box>
  );
}
