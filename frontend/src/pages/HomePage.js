import React from 'react';
import { Box, Button, Typography, Container } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import { useNavigate } from 'react-router-dom';


export default function HomePage() {
  const navigate = useNavigate();
  const handleCreateProject = () => {
    navigate('/new-project'); // 跳转到 "/create-project" 页面
  };
  const handleEditProject = () => {
    navigate('/manage-project'); // 跳转到 "/edit-project" 页面
  };


  return (
    <Container
      sx={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '90vh',
        textAlign: 'center',
      }}
    >

      <Typography variant="h5" sx={{ mb: 4 }}>
        A Multi-Agent System designed to
      </Typography>
      <Typography variant="h5" sx={{ mb: 4 }}>
        Automate the comprehensive biomedical research process.
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Button
          variant="contained"
          color="primary"
          size="large"
          startIcon={<AddIcon />}
          onClick={handleCreateProject}
          sx={{ textTransform: 'none' }}
        >
          Create a new project
        </Button>

        <Button 
          variant="outlined"
          color="primary"
          size="large"
          startIcon={<EditIcon />}
          onClick={handleEditProject}
          sx={{ textTransform: 'none' }}
        >
          Open or Edit Existing Projects
        </Button>
      </Box>
    </Container>
  );
}
