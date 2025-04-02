import { configureStore } from '@reduxjs/toolkit';
import languageReducer from './features/languageSlice';
import quizReducer from './features/quizSlice';

export const store = configureStore({
  reducer: {
    language: languageReducer,
    quiz: quizReducer
  }
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch; 