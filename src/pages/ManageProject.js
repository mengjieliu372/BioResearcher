import * as React from 'react';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Container from '@mui/material/Container';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import TablePagination from '@mui/material/TablePagination';
import TableFooter from '@mui/material/TableFooter';
import { useNavigate } from 'react-router-dom';

function createData(id, name) {
  return { id, name };
}

const rows = [
  createData(1, '实验A'),
  createData(2, '实验B'),
  createData(3, '实验C'),
  createData(4, '实验D'),
  createData(5, '实验E'),
  createData(6, '实验F'),
  createData(7, '实验G'),
  createData(8, '实验H'),
  createData(9, '实验I'),
  createData(10, '实验J'),
  createData(11, '实验K'),
  createData(12, '实验L'),
  createData(13, '实验M')
];

export default function BasicTable() {
  const navigate = useNavigate();
  const [open, setOpen] = React.useState(false);
  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(5);

  // State for the edited experiment details
  const [editedName, setEditedName] = React.useState('');

  const handleOpen = (id) => {
    navigate(`/${id}/steps`);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleEdit = (name) => {
    setEditedName(name); // Set the name of the experiment to be edited
    setOpen(true); // Open the dialog
  };

  const handleDelete = (name) => {
    console.log(`Deleting ${name}`);
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage); // 更新当前页
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10)); // 更新每页显示条数
    setPage(0); // 重置回第一页
  };

  const handleSave = () => {
    // Handle the save action, like sending the updated info to the server
    console.log('Updated experiment name:', editedName);
    setOpen(false); // Close the dialog after saving
  };

  const currentRows = rows.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  const emptyRows = page > 0 ? Math.max(0, (1 + page) * rowsPerPage - rows.length) : 0;

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
        <Table sx={{ minWidth: 650 }} aria-label="simple table">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell align="center">实验名称</TableCell>
              <TableCell align="center">操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {currentRows.map((row) => (
              <TableRow
                key={row.id}
                sx={{
                  '&:last-child td, &:last-child th': { border: 0 },
                  height: '7vh',
                }}
              >
                <TableCell component="th" scope="row">{row.id}</TableCell>
                <TableCell align="center">{row.name}</TableCell>
                <TableCell align="center">
                  <Button
                    variant="outlined"
                    color="primary"
                    onClick={() => handleOpen(row.id)}
                    sx={{ marginRight: 1, textTransform: 'none' }}
                  >
                    Open
                  </Button>
                  <Button
                    variant="outlined"
                    color="secondary"
                    onClick={() => handleEdit(row.name)}
                    sx={{ marginRight: 1, textTransform: 'none' }}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={() => handleDelete(row.name)}
                    sx={{ textTransform: 'none' }}
                  >
                    Delete
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {emptyRows > 0 && (
              <TableRow style={{ height: `${7 * emptyRows}vh` }}>
                <TableCell colSpan={3} />
              </TableRow>
            )}
          </TableBody>

          <TableFooter>
            <TableRow>
              <TablePagination
                rowsPerPageOptions={[5]}
                component="td"
                count={rows.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={handleChangePage}
                onRowsPerPageChange={handleChangeRowsPerPage}
              />
            </TableRow>
          </TableFooter>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>Edit the Project</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Modify the experiment details here:
          </DialogContentText>
          <TextField
            autoFocus
            required
            margin="dense"
            id="experiment-name"
            label="实验名称"
            value={editedName}
            onChange={(e) => setEditedName(e.target.value)}
            fullWidth
            variant="standard"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSave}>Save</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
