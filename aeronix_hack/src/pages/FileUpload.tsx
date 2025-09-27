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
  const [csv, setCsv] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [progress, setProgress] = useState(0);

  const handleNetlistChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files || []);
    const allowedTypes = ["application/ipc", "application/d356"];
    const validNetlists = selected.filter((f) => allowedTypes.includes(f.type));
    console.log(selected);
    if (e.target.files) setNetlist(e.target.files[0]);
    setProgress(0);
    setMessage("");
  };

  const handleCsvChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files || []);
    const allowedTypes = ["application/csv"];
    const validCsv = selected.filter((f) => allowedTypes.includes(f.type));
    console.log(selected);
    if (e.target.files) setCsv(e.target.files[0]);
    setProgress(0);
    setMessage("");
  };

  const handleUpload = async () => {
    if (!netlist) return;
    const netlistData = new FormData();
    netlistData.append("file", netlist);
    const csvData = new FormData();
    csvData.append("file", csv);

    try {
      const response = await axios.post(
        "http://localhost:5000/upload",
        { netlist: netlistData, csv: csvData },
        {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (event) => {
            setProgress(
              Math.round((event.loaded * 100) / (event.total ? event.total : 1))
            );
          },
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
              id="file-upload"
              multiple={false}
              style={{ display: "none" }}
              onChange={handleNetlistChange}
            />
            <label htmlFor="file-upload">
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
              id="file-upload"
              multiple={false}
              style={{ display: "none" }}
              onChange={handleCsvChange}
            />
            <label htmlFor="file-upload">
              <Stack spacing={3}>
                <Button
                  variant="contained"
                  component="span"
                  startIcon={<CloudUploadIcon />}
                  sx={{ mb: 2 }}
                >
                  Csv Bill of Materials File (.csv)
                </Button>
                {csv && <Typography>{csv.name}</Typography>}
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

          {progress > 0 && (
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{ mt: 2 }}
            />
          )}

          {message && <Typography sx={{ mt: 2 }}>{message}</Typography>}
        </ThemeProvider>
      </Paper>
    </Box>
  );
};

export default FileUpload;
