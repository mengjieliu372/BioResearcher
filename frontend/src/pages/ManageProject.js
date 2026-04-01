import * as React from 'react';
import Container from '@mui/material/Container';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableFooter from '@mui/material/TableFooter';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import Grid from '@mui/material/Grid2';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import { useNavigate } from 'react-router-dom';
import { useEffect, useMemo, useState } from 'react';
import { deleteProject, getProjects, pauseExperiment, updateProject } from '../services/api';
import { consumeWelcomeNotice, getAuthUser } from '../utils/auth';

function toRows(projects) {
  return (projects || []).map((p) => ({
    id: p.id,
    name: p.expName,
    owner: p.owner_username || 'system',
    raw: p,
  }));
}

export default function ManageProject() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [projects, setProjects] = useState([]);
  const [welcomeMsg, setWelcomeMsg] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  const [editing, setEditing] = useState(null);
  const authUser = getAuthUser();
  const isSuperuser = Boolean(authUser?.is_superuser);

  const refreshProjects = async () => {
    try {
      const response = await getProjects();
      const payload = response?.data;
      setProjects(Array.isArray(payload) ? payload : []);
    } catch (e) {
      console.log('Failed to fetch projects:', e);
      setProjects([]);
    }
  };

  useEffect(() => {
    refreshProjects();
  }, []);

  useEffect(() => {
    const info = consumeWelcomeNotice();
    if (!info?.message) return;
    setWelcomeMsg(info.message);
  }, []);

  const rows = useMemo(() => toRows(projects), [projects]);
  const currentRows = rows.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  const emptyRows = Math.max(0, (1 + page) * rowsPerPage - rows.length);

  const handleOpenProject = (id) => {
    navigate(`/${id}/steps/search`);
  };

  const handleEdit = (id) => {
    const project = projects.find((x) => x.id === id);
    if (!project) return;
    setEditing({ ...project });
    setOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this project?')) return;
    await deleteProject(id);
    await refreshProjects();
  };

  const handleForcePause = async (id) => {
    try {
      await pauseExperiment(id);
      alert(`Project ${id} pause requested.`);
    } catch (e) {
      console.log(e);
      alert('Failed to pause project.');
    }
  };

  const handleSave = async () => {
    if (!editing) return;
    if (!editing.expName || !editing.expPurpose || !editing.expCondition || !editing.expRequirement) {
      alert('璇峰～鍐欏疄楠岀浉鍏充俊鎭紒');
      return;
    }
    if (!Object.values(editing.paperset || {}).some(Boolean)) {
      alert('璇烽€夋嫨瑕佹绱㈢殑鏂囩尞搴擄紒');
      return;
    }
    if (!Object.values(editing.dataset || {}).some(Boolean)) {
      alert('请选择要检索的数据集库！');
      return;
    }
    try {
      await updateProject(editing);
      setOpen(false);
      setEditing(null);
      await refreshProjects();
    } catch (e) {
      console.log('Failed to update project:', e);
    }
  };

  return (
    <Container
      sx={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'flex-start',
        textAlign: 'center',
        width: '100%',
        height: '90vh',
      }}
    >
      <TableContainer
        component={Paper}
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.2)',
          borderRadius: '8px',
          boxShadow: 3,
          height: '49vh',
        }}
      >
        <Table sx={{ minWidth: 650 }} aria-label="project table">
          <TableHead>
            <TableRow>
              <TableCell align="center">ID</TableCell>
              <TableCell align="center">Experiment Name</TableCell>
              <TableCell align="center">Owner</TableCell>
              <TableCell align="center">Operations</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {currentRows.map((row) => (
              <TableRow key={row.id} sx={{ '&:last-child td, &:last-child th': { border: 0 }, height: '7vh' }}>
                <TableCell align="center">{row.id}</TableCell>
                <TableCell align="center">{row.name}</TableCell>
                <TableCell align="center">{row.owner}</TableCell>
                <TableCell align="center">
                  <Button variant="outlined" color="primary" onClick={() => handleOpenProject(row.id)} sx={{ mr: 1, textTransform: 'none' }}>
                    Open
                  </Button>
                  <Button variant="outlined" color="secondary" onClick={() => handleEdit(row.id)} sx={{ mr: 1, textTransform: 'none' }}>
                    Edit
                  </Button>
                  <Button variant="outlined" color="error" onClick={() => handleDelete(row.id)} sx={{ textTransform: 'none' }}>
                    Delete
                  </Button>
                  {isSuperuser ? (
                    <Button variant="outlined" color="warning" onClick={() => handleForcePause(row.id)} sx={{ ml: 1, textTransform: 'none' }}>
                      Force Pause
                    </Button>
                  ) : null}
                </TableCell>
              </TableRow>
            ))}
            {emptyRows > 0 ? (
              <TableRow style={{ height: `${7 * emptyRows}vh` }}>
                <TableCell colSpan={4} />
              </TableRow>
            ) : null}
          </TableBody>
          <TableFooter>
            <TableRow>
              <TablePagination
                rowsPerPageOptions={[5]}
                component="td"
                count={rows.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={(event, newPage) => setPage(newPage)}
                onRowsPerPageChange={(event) => {
                  setRowsPerPage(parseInt(event.target.value, 10));
                  setPage(0);
                }}
              />
            </TableRow>
          </TableFooter>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit the Project</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item="true" size={12}>
              <TextField
                label="Experiment Name"
                variant="outlined"
                required
                fullWidth
                value={editing?.expName || ''}
                onChange={(e) => setEditing((prev) => ({ ...prev, expName: e.target.value }))}
              />
            </Grid>
            <Grid item="true" size={12}>
              <TextField
                label="Experiment Purpose"
                variant="outlined"
                required
                fullWidth
                value={editing?.expPurpose || ''}
                onChange={(e) => setEditing((prev) => ({ ...prev, expPurpose: e.target.value }))}
              />
            </Grid>
            <Grid item="true" size={12}>
              <TextField
                label="Experiment Condition"
                variant="outlined"
                required
                multiline
                rows={3}
                fullWidth
                value={editing?.expCondition || ''}
                onChange={(e) => setEditing((prev) => ({ ...prev, expCondition: e.target.value }))}
              />
            </Grid>
            <Grid item="true" size={12}>
              <TextField
                label="Experiment Requirement"
                variant="outlined"
                required
                multiline
                rows={3}
                fullWidth
                value={editing?.expRequirement || ''}
                onChange={(e) => setEditing((prev) => ({ ...prev, expRequirement: e.target.value }))}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={handleSave}>Save</Button>
        </DialogActions>
      </Dialog>


      <Snackbar
        open={Boolean(welcomeMsg)}
        autoHideDuration={5000}
        onClose={() => setWelcomeMsg('')}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={() => setWelcomeMsg('')} severity="success" sx={{ width: '100%' }}>
          {welcomeMsg}
        </Alert>
      </Snackbar>
    </Container>
  );
}
