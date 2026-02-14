"""
Test to verify logging improvements for the training system integration.
This test ensures that the logging changes properly capture API interactions.
"""
import unittest
import logging
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestLoggingImprovements(unittest.TestCase):
    """Test that logging improvements work correctly."""

    def test_logging_configuration(self):
        """Verify that CPTChecker logger is configured."""
        logger = logging.getLogger("CPTChecker")
        self.assertIsNotNone(logger)
        # Logger should exist even if not configured yet
        self.assertTrue(hasattr(logger, 'info'))
        self.assertTrue(hasattr(logger, 'error'))
        self.assertTrue(hasattr(logger, 'warning'))

    @patch('aiohttp.ClientSession')
    @patch('src.cogs.cpt_checker.logger')
    async def test_fetch_cpts_logs_token_status(self, mock_logger, mock_session):
        """Test that fetch_cpts logs whether token is configured."""
        from src.cogs.cpt_checker import CPTChecker
        from src import config
        
        # Mock the bot
        mock_bot = MagicMock()
        checker = CPTChecker(mock_bot)
        
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": []})
        
        mock_session_instance = AsyncMock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)
        mock_session_instance.get = MagicMock(return_value=mock_response)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.return_value = mock_session_instance
        
        # Test with token
        original_token = config.TRAINING_API_TOKEN
        try:
            config.TRAINING_API_TOKEN = "test_token_123"
            await checker.fetch_cpts()
            
            # Verify INFO level logging was called for token
            info_calls = [str(call) for call in mock_logger.info.call_args_list]
            self.assertTrue(any("Bearer token" in str(call) for call in info_calls),
                          "Should log Bearer token usage")
            
            # Test without token
            mock_logger.reset_mock()
            config.TRAINING_API_TOKEN = None
            await checker.fetch_cpts()
            
            # Verify WARNING was logged
            warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
            self.assertTrue(any("No TRAINING_API_TOKEN" in str(call) for call in warning_calls),
                          "Should warn when token is missing")
        finally:
            config.TRAINING_API_TOKEN = original_token

    def test_logging_levels_used_correctly(self):
        """Verify that logging uses INFO level for important messages."""
        import src.cogs.cpt_checker as cpt_module
        
        # Read the source code and verify INFO level is used
        with open(cpt_module.__file__, 'r') as f:
            source = f.read()
            
        # Should use INFO level for API fetching
        self.assertIn('logger.info(f"Fetching CPTs from', source)
        
        # Should use INFO level for processing
        self.assertIn('logger.info(f"Processing', source)
        
        # Should use INFO level for API response
        self.assertIn('logger.info(f"Raw API response:', source)

if __name__ == '__main__':
    # Run async tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLoggingImprovements)
    
    # Run synchronous tests
    for test in suite:
        if asyncio.iscoroutinefunction(test._testMethodName):
            # Convert async test to sync
            asyncio.run(test.debug())
        else:
            unittest.TextTestRunner(verbosity=2).run(test)
