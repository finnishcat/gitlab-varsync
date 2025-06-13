import React from "react";

export function Card({ children, className = "" }) {
  return (
    <div className={`bg-white border border-gray-200 rounded shadow-sm p-4 ${className}`}>
      {children}
    </div>
  );
}

export function CardContent({ children, className = "" }) {
  return <div className={`text-gray-700 ${className}`}>{children}</div>;
}
