import React from 'react';
import { Typography, Box } from '@mui/material';
import { ErrorOutline as ErrorIcon } from '@mui/icons-material';

export default function ErrorPage ({ code, message })  {
  // 处理错误信息
  const errorMessage = message;
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
          m: 'auto'
        }}
      >
        <ErrorIcon sx={{ fontSize: 100, color: 'error.main',}} />
        <Typography variant="h6" color="textSecondary">
          Error Code: {errorCode}
        </Typography>
        <Typography variant="body1">
          {errorMessage}
        </Typography>
      </Box>
  );
};
