import axios from "axios";
const API_URL = "http://45.66.10.106:8000/swagger/";
export const fetchData = async () => {
  const response = await axios.get(`${API_URL}`);
  return response.data;
};