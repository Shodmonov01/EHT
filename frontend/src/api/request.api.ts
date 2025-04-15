import axios from "axios";
import {
  QuizResult,
  QuizStartRequest,
  Category,
  CategoryQuestions,
} from "../types/quizs";
import { store } from "../redux/store";

const API_URL = import.meta.env.VITE_API_URL;

const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': '*/*'
  }
});

axiosInstance.interceptors.request.use((config) => {
  const state = store.getState();
  const currentLanguage = state.language.currentLanguage;
  
  
  config.headers['Accept-Language'] = currentLanguage;
  config.headers['Content-Type'] = 'application/json';
  
  return config;
}, (error) => {
  console.error('Request interceptor error:', error);
  return Promise.reject(error);
});

export const fetchCategories = async () => {
  const { data } = await axiosInstance.get<Category[]>(
    `/quiz/api/category-set/`
  );
  return data;
};

export const startQuiz = async (quizData: QuizStartRequest) => {
  const { data } = await axiosInstance.post<QuizResult>(
    `/quiz/api/quizzes/start`,
    quizData
  );
  return data;
};

export const fetchQuestions = async (categorySetId: number) => {
  try {

    const { data } = await axiosInstance.get<CategoryQuestions[]>(
      `/quiz/api/quiz/questions/${categorySetId}/`
    );
    return data;
  } catch (error) {
    console.error('Error fetching questions:', error);
    throw error;
  }
};
export const submitQuiz = async (userToken: string, answers: number[], unansweredQuestionIds: number[]) => {
  const requestBody = {
    user_token: userToken,
    answer_ids: answers,
    unanswered_question_ids: unansweredQuestionIds
  };
  

  try {
    const { data } = await axiosInstance.post(`/quiz/api/quiz/submit`, requestBody);
    return data;
  } catch (error) {
    console.error("submitQuiz xatolik:", error);
    throw error;
  }
};

export const getQuizResultById = async (id: number) => {
  const { data } = await axiosInstance.get<QuizResult>(
    `/quiz/api/quizzes/quiz-results/${id}/`
  );
  return data;
};

export const categoryKeys = {
  all: ["categories"] as const,
};

export const quizKeys = {
  all: ["quizzes"] as const,
  start: () => [...quizKeys.all, "start"] as const,
};