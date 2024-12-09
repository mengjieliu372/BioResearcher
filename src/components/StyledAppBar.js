import * as React from 'react';
import { styled, alpha } from '@mui/material/styles';
import Box from '@mui/material/Box';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';
import { useNavigate } from 'react-router-dom';

const StyledToolbar = styled(Toolbar)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  flexShrink: 0,
  borderRadius: `calc(${theme.shape.borderRadius}px + 8px)`,
  backdropFilter: 'blur(24px)',
  border: '1px solid',
  borderColor: theme.palette.divider,
  backgroundColor: alpha(theme.palette.background.default, 0.4),
  boxShadow: theme.shadows[1],
  padding: '3px 12px',
}));

export default function StyledAppBar() {
  const navigate = useNavigate();
  const handleHomePage = () => {
    navigate('/');
  };

  const handleNewProject = () => {
    navigate('/new-project');
  };

  const handleManageProject = () => {
    navigate('/manage-project');
  }

  return (
    <div>
      <Container
        sx={{
          height: '10vh',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center'
        }}
      >
      </Container>
      <AppBar
        position="fixed"
        enableColorOnDark
        sx={{
          boxShadow: 0,
          bgcolor: 'transparent',
          backgroundImage: 'none',
          mt: '20px'
        }}
      >
        <Container maxWidth="lg">
          <StyledToolbar variant="dense" disableGutters>
            <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', px: 0 }}>

              <Box sx={{ display: { xs: 'none', md: 'flex' } }}>
                <img src='/logo.png' alt="Logo" style={{ height: 30, width: 'auto' }} />

                <Button 
                  variant="text"
                  color="success"
                  size="small"
                  onClick={handleHomePage}
                  sx={{
                    textTransform: 'none',
                    color: 'gray',
                    ml: 3,
                    mr: 1
                  }}
                >
                  HomePage
                </Button>

                <Button 
                  variant="text"
                  color="success"
                  size="small"
                  onClick={handleNewProject}
                  sx={{
                    textTransform: 'none',
                    color: 'gray',
                    ml: 1,
                    mr: 2
                  }}
                >
                  New Project
                </Button>

                <Button 
                  variant="text"
                  color="success"
                  size="small"
                  onClick={handleManageProject}
                  sx={{
                    textTransform: 'none',
                    color: 'gray',
                    ml: 1,
                    mr: 2
                  }}
                >
                  Projects Manage
                </Button>
              </Box>
            </Box>
            <Box
              sx={{
                display: { xs: 'none', md: 'flex' },
                gap: 1,
                alignItems: 'center',
              }}
            >
              <Button color="primary" variant="text" size="small">
                Sign in
              </Button>
              <Button color="primary" variant="contained" size="small">
                Sign up
              </Button>

            </Box>
          </StyledToolbar>
        </Container>
      </AppBar>
    </div>
  );
}