import logging 

def setup_logger(name: str) -> logging.Logger:
  """
    Set up a logger with consistent configuration.
    
    Args:
        name (str): Name of the logger (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
  logger = logging.getLogger(name)
  if not logger.handlers:
    logger.setLevel(logging.INFO)

    # Console Handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)

    # formatter
    formatter = logging.Formatter(
      '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger 