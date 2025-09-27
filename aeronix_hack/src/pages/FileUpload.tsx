// FileUpload.tsx
import React, { useState } from "react";
import axios from "axios";
import {
  Button,
  Typography,
  Box,
  LinearProgress,
  Paper,
  createTheme,
  ThemeProvider,
  Stack,
} from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";

const FileUpload: React.FC = () => {
  const [netlist, setNetlist] = useState<File | null>(null);
  const [xlsx, setxlsx] = useState<File | null>(null);
  const [message, setMessage] = useState<string>("");

  const handleNetlistChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files || []);
    console.log(selected);
    if (e.target.files) setNetlist(e.target.files[0]);
  };

  const handlexlsxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files || []);
    console.log(selected);
    if (e.target.files) setxlsx(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!netlist) return;
    if (!xlsx) return;
    const netlistData = new FormData();
    netlistData.append("file", netlist);
    const xlsxData = new FormData();
    xlsxData.append("file", xlsx);

    try {
      const response = await axios.post(
        "http://localhost:5000/upload",
        { netlist: netlistData, xlsx: xlsxData },
        {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (event) => {},
        }
      );
      setMessage(response.data.message);
    } catch (err) {
      setMessage("Upload failed");
    }
  };

  const baseTheme = createTheme();
  const theme = createTheme({
    typography: {
      fontFamily: '"Times New Roman", Times, serif',
      h3: {
        fontSize: "1.2rem",
        "@media (min-width:600px)": {
          fontSize: "1.5rem",
        },
        // assuming baseTheme is defined elsewhere
        [baseTheme.breakpoints.up("md")]: {
          fontSize: "2.4rem",
        },
      },
    },
  });

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      height="100vh"
      bgcolor="#0"
    >
      <Paper
        elevation={3}
        sx={{
          padding: 4,
          textAlign: "center",
          width: 400,
          borderRadius: "16px",
        }}
      >
        <ThemeProvider theme={theme}>
          <Stack spacing={3}>
            <input
              type="file"
              id="netlist-upload"
              accept=".d356,.ipc"
              multiple={false}
              style={{ display: "none" }}
              onChange={handleNetlistChange}
            />
            <label htmlFor="netlist-upload">
              <Stack spacing={3}>
                <Button
                  variant="contained"
                  component="span"
                  startIcon={<CloudUploadIcon />}
                  sx={{ mb: 2 }}
                >
                  Netlist File (.d356 or .ipc)
                </Button>
                {netlist && <Typography>{netlist.name}</Typography>}
              </Stack>
            </label>
            <input
              type="file"
              id="xlsx-upload"
              accept=".xlsx"
              multiple={false}
              style={{ display: "none" }}
              onChange={handlexlsxChange}
            />
            <label htmlFor="xlsx-upload">
              <Stack spacing={3}>
                <Button
                  variant="contained"
                  component="span"
                  startIcon={<CloudUploadIcon />}
                  sx={{ mb: 2 }}
                >
                  Excel Bill of Materials File (.xlsx)
                </Button>
                {xlsx && <Typography>{xlsx.name}</Typography>}
              </Stack>
            </label>
          </Stack>

          <Box mt={2}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleUpload}
              disabled={!netlist}
            >
              Run Tool
            </Button>
          </Box>

          {message && <Typography sx={{ mt: 2 }}>{message}</Typography>}
        </ThemeProvider>
      </Paper>
    </Box>
  );
};

export default FileUpload;
