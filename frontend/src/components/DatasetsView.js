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

export default function DatasetsView({ query, data }) {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const { id } = useParams();
  console.log(query);
  console.log(typeof (query));
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
              <Typography variant='subtitle' sx={{ flexGrow: 1, fontWeight: 'bold' }}>{value.Title}</Typography>
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
              <Typography sx={{ fontWeight: 'bold', display: 'inline' }}>Search Query : </Typography>
              <Typography sx={{ display: 'inline' }}>{value.search_query}</Typography>
            </Box>
            <Box>
              <Typography sx={{ fontWeight: 'bold', display: 'inline' }}>Identifier:</Typography>
              <Typography sx={{ display: 'inline' }}>{key}</Typography>
            </Box>
            <Box>
              <Typography sx={{ fontWeight: 'bold', display: 'inline' }}>Status:</Typography>
              <Typography sx={{ display: 'inline' }}>{value.Status}</Typography>
            </Box>
            <Box>
              <Typography sx={{ fontWeight: 'bold' }}>Summary:</Typography>
              <Typography sx={{ color: 'text.secondary' }}>
                {value.Summary}
              </Typography>
            </Box>
          </AccordionDetails>
        </Accordion>
      ))
    );
  };


  return (
    <Box sx={{ width: '52vw' }}>
      <Typography variant="h6" sx={{color: '#108ee9'}}>
        Query:
      </Typography>
      <Typography variant="subtitle1">
        {query}
      </Typography>
      <Typography variant='h6' sx={{ mt: 1, color: '#108ee9'}}>
        Retrival Results:
      </Typography>
      <Box>
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
                width: '52vw',
                ml: 'auto',
                mr: 'auto',
                overflowY: 'auto',
                height: '53vh',
                maxHeight: '53vh',
                backgroundColor: '#f0f0f0',
                borderRadius: '8px',
                boxShadow: 3,
              }}
            >
              {showDatasets(data)}
            </Box>
          )
        }
      </Box>
    </Box>
  );
}
