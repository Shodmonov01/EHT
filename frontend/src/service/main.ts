// import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
// import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
// import React from 'react';
// import ReactDOM from 'react-dom/client';
// import App from '../App';

// const queryClient = new QueryClient({
//   defaultOptions: {
//     queries: {
//       staleTime: 1000 * 60 * 5, // 5 daqiqa
//       refetchOnWindowFocus: false,
//       retry: 1,
//     },
//   },
// });

// const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
// root.render(
//   <React.StrictMode>
//     <QueryClientProvider client={queryClient}>
//       <App />
//       <ReactQueryDevtools initialIsOpen={false} />
//     </QueryClientProvider>
//   </React.StrictMode>
// );
