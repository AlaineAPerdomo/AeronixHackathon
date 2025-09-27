// FileUpload.tsx
import React, { useState } from "react";
import axios from "axios";
import {
  Button,
  Typography,
  Box,
  Paper,
  createTheme,
  ThemeProvider,
  Stack,
} from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";

const FileUpload: React.FC = () => {
  const [netlist, setNetlist] = useState<File | null>(null);
  const [csv, setcsv] = useState<File | null>(null);
  const [message, setMessage] = useState<string>("");

  const handleNetlistChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files || []);
    console.log(selected);
    if (e.target.files) setNetlist(e.target.files[0]);
  };

  const handlecsvChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files || []);
    console.log(selected);
    if (e.target.files) setcsv(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!netlist) return;
    if (!csv) return;
    const formData = new FormData();
    formData.append("netlist", netlist);
    formData.append("csv", csv);

    try {
      const response = await axios.post(
        "http://localhost:5000/upload",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
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
              id="csv-upload"
              accept=".csv"
              multiple={false}
              style={{ display: "none" }}
              onChange={handlecsvChange}
            />
            <label htmlFor="csv-upload">
              <Stack spacing={3}>
                <Button
                  variant="contained"
                  component="span"
                  startIcon={<CloudUploadIcon />}
                  sx={{ mb: 2 }}
                >
                  Altium CSV Bill of Materials File (.csv)
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

          {message && <Typography sx={{ mt: 2 }}>{message}</Typography>}
        </ThemeProvider>
      </Paper>
    </Box>
  );
};

export default FileUpload;
