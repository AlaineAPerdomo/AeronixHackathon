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
} from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";

const FileUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [progress, setProgress] = useState(0);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) setFile(e.target.files[0]);
    setProgress(0);
    setMessage("");
  };

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        "http://localhost:5000/upload",
        formData,
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
          <Typography variant="h5" gutterBottom>
            Upload Your File
          </Typography>
          <input
            type="file"
            id="file-upload"
            style={{ display: "none" }}
            onChange={handleFileChange}
          />
          <label htmlFor="file-upload">
            <Button
              variant="contained"
              component="span"
              startIcon={<CloudUploadIcon />}
              sx={{ mb: 2 }}
            >
              Choose File
            </Button>
          </label>
          {file && <Typography>{file.name}</Typography>}
          <Box mt={2}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleUpload}
              disabled={!file}
            >
              Upload
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
