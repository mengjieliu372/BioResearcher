import React from 'react';
import { Typography, Box } from '@mui/material';
import { ErrorOutline as ErrorIcon } from '@mui/icons-material';

export default function ErrorPage({ code, message }) {
  const errorMessage = React.useMemo(() => {
    if (message === null || message === undefined) {
      return 'Unknown error';
    }
    if (typeof message === 'string') {
      return message;
    }
    if (typeof message === 'object') {
      try {
        return JSON.stringify(message, null, 2);
      } catch (e) {
        return String(message);
      }
    }
    return String(message);
  }, [message]);

  const errorCode = code;

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        flexDirection: 'column',
        height: '50vh',
        width: '50vw',
        textAlign: 'center',
        m: 'auto',
      }}
    >
      <ErrorIcon sx={{ fontSize: 100, color: 'error.main' }} />
      <Typography variant="h6" color="textSecondary">
        Error Code: {errorCode}
      </Typography>
      <Typography
        variant="body1"
        sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
      >
        {errorMessage}
      </Typography>
    </Box>
  );
}
