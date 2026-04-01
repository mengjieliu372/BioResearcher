import React, { useEffect, useMemo, useState } from 'react';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';

export default function LoadingProgress({
  label = 'Loading',
  stepPercent = 5,
  stepIntervalMs = 800,
  maxPercentBeforeDone = 95,
  progressValue = null,
  detail = '',
}) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (typeof progressValue === 'number') {
      setProgress(Math.max(0, Math.min(100, Math.round(progressValue))));
      return undefined;
    }
    const timer = setInterval(() => {
      setProgress((prev) => {
        const next = prev + stepPercent;
        return next >= maxPercentBeforeDone ? maxPercentBeforeDone : next;
      });
    }, stepIntervalMs);

    return () => clearInterval(timer);
  }, [stepPercent, stepIntervalMs, maxPercentBeforeDone, progressValue]);

  const etaSeconds = useMemo(() => {
    if (progress >= 100) return 0;
    const remainPercent = 100 - progress;
    const remainSteps = Math.ceil(remainPercent / stepPercent);
    return Math.ceil((remainSteps * stepIntervalMs) / 1000);
  }, [progress, stepPercent, stepIntervalMs]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 1,
        py: 4,
      }}
    >
      <Box sx={{ position: 'relative', display: 'inline-flex' }}>
        <CircularProgress variant="determinate" value={progress} size={72} thickness={4.8} />
        <Box
          sx={{
            top: 0,
            left: 0,
            bottom: 0,
            right: 0,
            position: 'absolute',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography variant="caption" component="div" color="text.secondary">
            {`${progress}%`}
          </Typography>
        </Box>
      </Box>
      <Typography variant="body1" sx={{ fontWeight: 500 }}>
        {label}
      </Typography>
      {typeof progressValue === 'number' ? (
        <Typography variant="body2" color="text.secondary">
          Server progress mode
        </Typography>
      ) : (
        <Typography variant="body2" color="text.secondary">
          Estimated time left: ~{etaSeconds}s
        </Typography>
      )}
      {detail ? (
        <Typography variant="body2" color="text.secondary">
          {detail}
        </Typography>
      ) : null}
    </Box>
  );
}
