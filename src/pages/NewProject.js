import * as React from 'react';
import { useState } from 'react';
import { Container, Box, TextField, Typography, FormGroup, FormControlLabel, Checkbox, Radio, RadioGroup, FormControl, Button, List, ListItem, ListItemText, IconButton } from '@mui/material';
import Grid from '@mui/material/Grid2';
import { styled } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DeleteIcon from '@mui/icons-material/Delete';

const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});

export default function NewProject() {
  // State for input values
  // 实验名称 实验目的 实验条件 实验要求
  const [expName, setExpName] = useState('');
  const [expPurpose, setExpPurpose] = useState('');
  const [expCondition, setExpCondition] = useState('');
  const [expRequirement, setExpRequirement] = useState('');
  const [paper, setPaper] = useState({ PMC: true, PubMed: false});
  const [dataset, setDataset] = useState({ GEO: true, NCBI: false, cBioPortal: false});

  const [llmModel, setLLMModel] = useState('GPT4o');
  const [refNum, setRefNum] = useState();
  const [reviewerRound, setReviewerRound] = useState();
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleInputRefNum = (event) => {
    const newValue = event.target.value.replace(/[^0-9]/g, '');
    setRefNum(newValue);
  };

  const handleInputReviewerRound = (event) => {
    const newValue = event.target.value.replace(/[^0-9]/g, '');
    setReviewerRound(newValue);
  };

  const handlePaperChange = (event) => {
    setPaper(prev => ({
      ...prev,
      [event.target.name]: event.target.checked
    }));
  };

  const handleDatabaseChange = (event) => {
    setDataset(prev => ({
      ...prev,
      [event.target.name]: event.target.checked
    }));
  };

  const handleFileChange = (event) => {
    const files = Array.from(event.target.files);
    setUploadedFiles(prevFiles => [...prevFiles, ...files]);
  };

  const handleFileDelete = (fileName) => {
    setUploadedFiles(prevFiles => prevFiles.filter(file => file.name !== fileName));
  };

  const handleLlmModelChange = (event) => {
    setLLMModel(event.target.value);
  };
  
  const handleSubmit = () => {
    // 数据验证
    if (!expName || !expPurpose || !expCondition || !expRequirement) {
      alert('请填写实验相关信息！');
      return;
    }
    
    // 检查paper和dataset是否全为false
    if (!Object.values(paper).some(Boolean)) {
      alert('请选择要检索的文献库！');
      return;
    }
    if (!Object.values(dataset).some(Boolean)) {
      alert('请选择要检索的数据集库！');
      return;
    }
    
    const formData = {
      expName,
      expPurpose,
      expCondition,
      expRequirement,
      paper,
      dataset,
      llmModel,
      refNum,
      reviewerRound,
      uploadedFiles: uploadedFiles.map(file => file.name), // 上传文件名称数组
    };
  
    console.log('提交的数据:', formData);
  
  
    alert('表单已提交！'); // 显示成功提交的提示
  };
  

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Container
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          width: '60%',
          maxWidth: 800,
          backgroundColor: 'white',
          borderRadius: 8,
          padding: 4,
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.1)',
          p: 4,
          mb: 8,
        }}
      >
        <Typography variant="h4" sx={{ mb: 4, fontWeight: 'bold', color: '#333' }}>
          Create a New Project
        </Typography>

        <Grid container spacing={2}>
          <Grid item="true" size={12}>
            <TextField
              label="实验名称"
              variant="outlined"
              required
              fullWidth
              sx={{ mb: 2 }}
              value={expName}
              onChange={(e) => setExpName(e.target.value)}
            />
          </Grid>

          <Grid item="true" size={12}>
            <TextField
              label="实验目的"
              variant="outlined"
              required
              fullWidth
              sx={{ mb: 2 }}
              value={expPurpose}
              onChange={(e) => setExpPurpose(e.target.value)}
            />
          </Grid>

          <Grid item="true" size={12}>
            <TextField
              label="实验条件"
              variant="outlined"
              required
              multiline
              fullWidth
              rows={3}
              sx={{ mb: 2 }}
              value={expCondition}
              onChange={(e) => setExpCondition(e.target.value)}
            />
          </Grid>

          <Grid item="true" size={12}>
            <TextField
              label="实验要求"
              variant="outlined"
              required
              multiline
              fullWidth
              rows={3}
              sx={{ mb: 2 }}
              value={expRequirement}
              onChange={(e) => setExpRequirement(e.target.value)}
            />
          </Grid>
        </Grid>



        <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#333', mt: 4 }}>
          选择要检索的数据库
        </Typography>
        <Typography variant="h6" sx={{ color: '#555', mb: 1 }}>
          文献库：
        </Typography>
        <FormGroup row sx={{ mb: 2 }}>
          <FormControlLabel 
            control={<Checkbox checked={paper.PMC} onChange={handlePaperChange} name='PMC'/>} 
            label="PMC" />
          <FormControlLabel 
            control={<Checkbox checked={paper.PubMed} onChange={handlePaperChange} name='PubMed'/>} 
            label="PubMed" />
        </FormGroup>
        <Typography variant="h6" sx={{ color: '#555', mb: 1 }}>
          数据集库：
        </Typography>
        <FormGroup row sx={{ mb: 2 }}>
          <FormControlLabel
            control={<Checkbox checked={dataset.GEO} onChange={handleDatabaseChange} name='GEO'/>} 
            label="GEO" />
          <FormControlLabel 
            control={<Checkbox  checked={dataset.NCBI} onChange={handleDatabaseChange} name='NCBI'/>}
            label="NCBI" />
          <FormControlLabel
            control={<Checkbox checked={dataset.cBioPortal} onChange={handleDatabaseChange} name='cBioPortal'/>} 
            label="cBioPortal" />
        </FormGroup>

        <Typography variant="h6" sx={{ color: '#555', mb: 1 }}>
          本地文献：
        </Typography>
        <Button
          component="label"
          role={undefined}
          variant="contained"
          tabIndex={-1}
          startIcon={<CloudUploadIcon />}
          sx={{ mb: 2 }}
        >
          Upload files
          <VisuallyHiddenInput
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            multiple
          />
        </Button>

        {uploadedFiles.length > 0 && (
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" sx={{ color: '#555', mb: 1 }}>
              已上传的文件：
            </Typography>
            <List>
              {uploadedFiles.map((file) => (
                <ListItem key={file.name} sx={{ display: 'flex', alignItems: 'center' }}>
                  <ListItemText primary={file.name} />
                  <IconButton onClick={() => handleFileDelete(file.name)}>
                    <DeleteIcon />
                  </IconButton>
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#333', mb: 2 }}>
          LLM模型选择
        </Typography>

        <FormControl>
          <RadioGroup
            row
            defaultValue="GPT4o"
            aria-labelledby="llm"
            onChange={handleLlmModelChange}
            name="row-radio-buttons-group"
            sx={{ mb: 4 }}
          >
            <FormControlLabel value="GPT4o" control={<Radio />} label="GPT4o" />
            <FormControlLabel value="gemini" control={<Radio />} label="gemini" />
            <FormControlLabel value="claude" control={<Radio />} label="claude" />
          </RadioGroup>
        </FormControl>

        <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#333', mb: 2 }}>
          其他可选参数
        </Typography>

        <Grid container spacing={2}>
          <Grid item="true" size={6}>
            <TextField
              label="参考文献的数量"
              variant="outlined"
              value={refNum}
              onInput={handleInputRefNum}
              fullWidth
            />
          </Grid>
          <Grid item="true" size={6}>
            <TextField
              label="Reviewer最大轮次"
              variant="outlined"
              value={reviewerRound}
              onInput={handleInputReviewerRound}
              fullWidth
            />
          </Grid>
        </Grid>

        <Button
          variant="contained"
          color="primary"
          size="large"
          sx={{ mt: 4 }}
          onClick={handleSubmit}
        >
          提交
        </Button>
      </Container>
    </Box>
  );
}
