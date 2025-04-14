import axios from "axios";
// const API_URL = "http://45.66.10.106:8000/swagger/";
const API_URL = "http://176.124.210.145:8000/swagger/";
// const API_URL = "https://e0e4-95-214-210-70.ngrok-free.app/";
export const fetchData = async () => {
  const response = await axios.get(`${API_URL}`);
  return response.data;
};