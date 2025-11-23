import React from 'react';
import { clsx } from 'clsx';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

const Card: React.FC<CardProps> = ({ className, children, ...props }) => {
  return (
    <div
      className={clsx(
        "rounded-lg border border-gray-200 bg-white shadow-sm",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

const CardHeader: React.FC<CardProps> = ({ className, children, ...props }) => {
  return (
    <div
      className={clsx("flex flex-col space-y-1.5 p-6", className)}
      {...props}
    >
      {children}
    </div>
  );
};

const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  className,
  children,
  ...props
}) => {
  return (
    <h3
      className={clsx(
        "text-2xl font-semibold leading-none tracking-tight",
        className
      )}
      {...props}
    >
      {children}
    </h3>
  );
};

const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  className,
  children,
  ...props
}) => {
  return (
    <p
      className={clsx("text-sm text-gray-600", className)}
      {...props}
    >
      {children}
    </p>
  );
};

const CardContent: React.FC<CardProps> = ({ className, children, ...props }) => {
  return (
    <div className={clsx("p-6 pt-0", className)} {...props}>
      {children}
    </div>
  );
};

const CardFooter: React.FC<CardProps> = ({ className, children, ...props }) => {
  return (
    <div
      className={clsx("flex items-center p-6 pt-0", className)}
      {...props}
    >
      {children}
    </div>
  );
};

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };