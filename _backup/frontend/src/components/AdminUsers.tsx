// frontend/src/components/AdminUsers.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DataGrid, GridColDef, GridPaginationModel } from '@mui/x-data-grid'; // Added GridPaginationModel
import { Box, Button, TextField, Dialog, DialogTitle, DialogContent, DialogActions, FormControl, InputLabel, Select, MenuItem, Typography } from '@mui/material';
import { useAuthStore } from '../stores/authStore';
import { getUsers, updateUser, deleteUser, createUser } from '../services/api';

interface User {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
}

const AdminUsers = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ id: 0, email: '', password: '', role: 'user', is_active: true });
  const [isEdit, setIsEdit] = useState(false);
  const [page, setPage] = useState(0); // Current page index (0-based)
  const [pageSize, setPageSize] = useState(10); // Rows per page
  const [totalRowCount, setTotalRowCount] = useState(0); // Total number of users

  useEffect(() => {
    if (user?.role !== 'admin') {
      navigate('/');
      return;
    }
    fetchUsers();
  }, [user, navigate, page, pageSize]); // Added page and pageSize to dependency array

  const fetchUsers = async () => {
    setLoading(true);
    try {
      // Calculate skip based on current page (0-indexed) and pageSize
      const skip = page * pageSize;
      const response = await getUsers(skip, pageSize); // New call with pagination params

      if (response && response.items) {
        setUsers(response.items);
        setTotalRowCount(response.total);
      } else {
        // Handle cases where response or items might be undefined, though API should return UserListResponse
        setUsers([]);
        setTotalRowCount(0);
        console.error('Error fetching users: Invalid response structure', response);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      setUsers([]); // Clear users on error
      setTotalRowCount(0); // Reset total count on error
    }
    setLoading(false);
  };

  const handlePaginationModelChange = (model: GridPaginationModel) => {
    setPage(model.page);
    setPageSize(model.pageSize);
    // Data fetching will be triggered by the useEffect hook that depends on 'page' and 'pageSize'
  };

  const handleOpen = (user?: User) => {
    if (user) {
      setForm({ id: user.id, email: user.email, password: '', role: user.role, is_active: user.is_active });
      setIsEdit(true);
    } else {
      setForm({ id: 0, email: '', password: '', role: 'user', is_active: true });
      setIsEdit(false);
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleSave = async () => {
    try {
      if (isEdit) {
        await updateUser(form.id, {
          email: form.email,
          password: form.password || undefined,
          role: form.role,
          is_active: form.is_active,
        });
      } else {
        await createUser({
          email: form.email,
          password: form.password,
          role: form.role,
        });
      }
      fetchUsers();
      handleClose();
    } catch (error) {
      console.error('Error saving user:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Tem certeza que deseja deletar este usuário?')) {
      try {
        await deleteUser(id);
        fetchUsers();
      } catch (error) {
        console.error('Error deleting user:', error);
      }
    }
  };

  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 90 },
    { field: 'email', headerName: 'Email', width: 200 },
    { field: 'role', headerName: 'Role', width: 120 },
    { field: 'is_active', headerName: 'Ativo', width: 100, type: 'boolean' },
    {
      field: 'actions',
      headerName: 'Ações',
      width: 200,
      renderCell: (params) => {
        return (
          <>
            <Button variant="outlined" size="small" onClick={() => handleOpen(params.row)} sx={{ mr: 1 }}>
              Editar
            </Button>
            <Button variant="outlined" size="small" color="error" onClick={() => handleDelete(params.row.id)}>
              Deletar
            </Button>
          </>
        );
      },
    },
  ];

  if (user?.role !== 'admin') return null;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>Gerenciamento de Usuários</Typography>
      <Button variant="contained" onClick={() => handleOpen()} sx={{ mb: 2 }}>
        Novo Usuário
      </Button>
      <Box sx={{ height: 400, width: '100%' }}>
        <DataGrid
          rows={users}
          columns={columns}
          rowCount={totalRowCount}
          loading={loading}
          pageSizeOptions={[5, 10, 25]}
          paginationMode="server"
          onPaginationModelChange={handlePaginationModelChange}
          paginationModel={{ page, pageSize }}
          disableRowSelectionOnClick
          // autoHeight // Consider adding if not already there and appropriate
        />
      </Box>
      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>{isEdit ? 'Editar Usuário' : 'Novo Usuário'}</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="Email"
            fullWidth
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Senha"
            type="password"
            fullWidth
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            disabled={isEdit && !form.password}
          />
          <FormControl fullWidth margin="dense">
            <InputLabel>Role</InputLabel>
            <Select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
            >
              <MenuItem value="user">User</MenuItem>
              <MenuItem value="admin">Admin</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Status</InputLabel>
            <Select
              value={form.is_active ? 'active' : 'inactive'}
              onChange={(e) => setForm({ ...form, is_active: e.target.value === 'active' })}
            >
              <MenuItem value="active">Ativo</MenuItem>
              <MenuItem value="inactive">Inativo</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancelar</Button>
          <Button onClick={handleSave} variant="contained">Salvar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdminUsers;