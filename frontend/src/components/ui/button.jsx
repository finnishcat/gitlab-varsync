import React from "react";

export function Button({ children, className = "", variant, ...props }) {
  let base = "px-4 py-2 rounded text-sm font-medium transition ";

  let variantClasses = {
    ghost: "bg-transparent hover:bg-gray-200 text-gray-700",
    default: "bg-blue-600 text-white hover:bg-blue-700",
  };

  let classes = base + (variantClasses[variant] || variantClasses.default) + " " + className;

  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
}
