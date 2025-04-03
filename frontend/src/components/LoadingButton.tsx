import { motion } from "framer-motion";
import "../styles/LoadingButton.css";

interface LoadingButtonProps {
  isLoading: boolean;
  children: React.ReactNode;
  type?: "button" | "submit";
  onClick?: () => void;
  disabled?: boolean;
}

export default function LoadingButton({ 
  isLoading, 
  children, 
  type = "button",
  onClick,
  disabled
}: LoadingButtonProps) {
  return (
    <motion.button
      type={type}
      className={`loading-button ${isLoading ? 'is-loading' : ''}`}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      disabled={disabled || isLoading}
    >
      {isLoading ? (
        <motion.div 
          className="button-loader"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
      ) : children}
    </motion.button>
  );
}
