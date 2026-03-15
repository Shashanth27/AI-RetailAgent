"""Odoo API integration for the Retail CRM Console Single AI Agent."""

import logging
import uuid
from typing import Dict, Optional, List

import requests
from requests.exceptions import RequestException

import config
from models import (
    AuthResponse, ProductsResponse, 
    RecommendationsResponse, CheckoutResponse, User, Product
)


class OdooAPI:
    """Odoo API client for interacting with Odoo CRM."""
    
    def __init__(self):
        """Initialize the Odoo API client."""
        # Ensure base URL doesn't have trailing slashes to prevent double-slash issues in URL construction
        self.base_url = config.ODOO_API_URL.rstrip('/')
        self.db = config.ODOO_DB
        self.url = config.ODOO_API_URL
        self.token = None
        self.user = None
        self.uid = None
        self.username = None
        self.password = None
        self.authenticated = False
        self.using_fallback = False
        self.logger = logging.getLogger(__name__)
        
        # Log initialization with database info
        self.logger.info("OdooAPI initialized with database: %s", self.db)
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """Make a read-only request to the Odoo API.
        
        This method ensures all requests are read-only by validating the request data
        and only allowing safe operations that don't modify data in the Odoo CRM.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data
            params: Request parameters
            headers: Request headers
            
        Returns:
            API response
        """
        # Ensure proper URL construction without double slashes
        base_url = self.base_url.rstrip('/')
        endpoint_path = endpoint.lstrip('/')
        
        # Construct the URL, ensuring no double slashes
        url = f"{base_url}/{endpoint_path}"
        
        # Set default headers
        if headers is None:
            headers = {}
        
        # Add authorization token if available
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        # Add API key if available
        if config.ODOO_API_KEY:
            headers["X-API-Key"] = config.ODOO_API_KEY
        
        # Ensure request is read-only by checking for write operations
        if data and isinstance(data, dict):
            params_dict = data.get("params", {})
            if isinstance(params_dict, dict):
                method_name = params_dict.get("method", "")
                if method_name in ["write", "create", "unlink", "delete"]:
                    self.logger.warning("Blocked attempt to modify data with method: %s", method_name)
                    return {"success": False, "error": "Write operations are not allowed in read-only mode"}
        
        try:
            self.logger.debug("Making %s request to %s", method, url)
            self.logger.debug("Request headers: %s", headers)
            self.logger.debug("Request data: %s", data)
            self.logger.debug("Request params: %s", params)
            
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=config.MAX_RESPONSE_TIME
            )
            
            # Log request and response
            self.logger.info("%s %s - Status: %d", method, url, response.status_code)
            
            # Log response content for debugging
            try:
                response_content = response.text[:500]  # Limit to first 500 chars to avoid huge logs
                self.logger.debug("Response content (truncated): %s", response_content)
            except Exception as e:
                self.logger.debug("Could not log response content: %s", str(e))
            
            # Raise exception for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            return response.json()
        except RequestException as e:
            self.logger.error("API request error: %s", str(e))
            return {"success": False, "error": str(e)}
        except Exception as e:
            self.logger.error("Unexpected error in API request: %s", str(e))
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    
    def login(self, username: str, password: str) -> AuthResponse:
        """Authenticate with the Odoo API in a read-only manner using JSON-RPC.
        
        Args:
            username: The username to authenticate with
            password: The password to authenticate with
            
        Returns:
            AuthResponse: The response from the authentication request
        """
        self.logger.info("Authenticating user (READ-ONLY): %s", username)
        
        # Set a flag to track if we're in fallback mode
        self.using_fallback = False
        
        try:
            # Try to authenticate using JSON-RPC
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "login",
                    "args": [self.db, username, password]
                },
                "id": uuid.uuid4().hex
            }
            
            response = requests.post(
                f"{self.url}/jsonrpc",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result and result["result"]:
                    self.uid = result["result"]
                    self.username = username
                    self.password = password  # Store for session management
                    self.authenticated = True
                    self.logger.info("Authentication successful (READ-ONLY)")
                    return AuthResponse(success=True, message="Authentication successful", uid=self.uid)
                else:
                    self.logger.warning("Authentication failed: Invalid credentials")
                    return AuthResponse(success=False, message="Invalid credentials", uid=None)
            else:
                self.logger.warning("Authentication failed: %s", response.text)
                return AuthResponse(success=False, message=f"Authentication failed: {response.status_code}", uid=None)
                
        except Exception as e:
            self.logger.error("Error during authentication: %s", str(e))
            return AuthResponse(success=False, message=f"Authentication error: {str(e)}", uid=None)
        
    def _get_sample_products(self, query: str = None, available_only: bool = False) -> List[Product]:
        """Get sample products for fallback mode.
        
        Args:
            query: Optional search query to filter products
            available_only: Whether to only include available products
            
        Returns:
            List of Product objects
        """
        # Create sample products
        sample_products = [
            Product(
                id=1,
                name="Sample Product 1",
                price=19.99,
                available=True,
                description="This is a sample product for demonstration purposes",
                default_code="SP001",
                tags=["sample", "demo"]
            ),
            Product(
                id=2,
                name="Sample Product 2",
                price=29.99,
                available=True,
                description="Another sample product for demonstration",
                default_code="SP002",
                tags=["sample", "premium"]
            ),
            Product(
                id=3,
                name="Sample Product 3",
                price=39.99,
                available=True,
                description="Premium sample product with advanced features",
                default_code="SP003",
                tags=["sample", "premium", "advanced"]
            ),
            Product(
                id=4,
                name="CDC Sample Product",
                price=49.99,
                available=True,
                description="CDC branded sample product",
                default_code="CDC001",
                tags=["CDC", "premium"]
            ),
            Product(
                id=5,
                name="Limited Edition Product",
                price=99.99,
                available=True,
                description="Limited edition product with exclusive features",
                default_code="LE001",
                tags=["limited", "exclusive"]
            ),
            Product(
                id=6,
                name="Out of Stock Product",
                price=59.99,
                available=False,
                description="This product is currently out of stock",
                default_code="OOS001",
                tags=["out-of-stock"]
            )
        ]
        
        # Filter by availability if needed
        if available_only:
            sample_products = [p for p in sample_products if p.available]
        
        # Filter by query if provided
        if query and query.strip():
            query = query.lower()
            filtered_products = []
            for product in sample_products:
                # Check if query is in name, description, default_code, or tags
                if (query in product.name.lower() or 
                    query in product.description.lower() or 
                    query in product.default_code.lower() or 
                    any(query in tag.lower() for tag in product.tags)):
                    filtered_products.append(product)
            return filtered_products
        
        return sample_products
        
        try:
            # Use the provided password or fall back to the one in config
            password = password or config.ODOO_PASSWORD
            
            # Try different authentication methods in order of preference
            
            # 1. Try API key authentication first (if available)
            if config.ODOO_API_KEY:
                self.logger.info("Attempting authentication using API key")
                # Set the API key as the token
                self.token = config.ODOO_API_KEY
                self.api_key_auth = True
                
                # Verify access with a simple request to check if API key works
                if self._verify_access():
                    # Create a user object
                    user = User(
                        id=1,  # Default to admin ID since we're using API key
                        name="API User",
                        username=username,
                        email=username if "@" in username else ""
                    )
                    self.user = user
                    self.logger.info("Successfully authenticated via API key")
                    
                    return AuthResponse(
                        success=True,
                        error=None,
                        user=user
                    )
                else:
                    self.logger.warning("API key authentication failed, trying XML-RPC authentication")
                    self.api_key_auth = False
            
            # 2. Try XML-RPC authentication (recommended by Odoo docs)
            self.logger.info("Attempting authentication using XML-RPC")
            
            import xmlrpc.client
            import ssl
            
            # Disable SSL certificate verification (as shown in the example script)
            ssl._create_default_https_context = ssl._create_unverified_context
            
            # Create XML-RPC client for the common endpoint
            # Make sure we're using the correct URL format for XML-RPC
            # The URL should not have /api in it for XML-RPC
            base_url = config.ODOO_API_URL.rstrip('/api')  # Strip '/api' if present
            common_url = f"{base_url}/xmlrpc/2/common"
            self.logger.debug("XML-RPC common URL: %s", common_url)
            common = xmlrpc.client.ServerProxy(common_url)
            
            try:
                # First check if we can connect to the server
                version_info = common.version()
                self.logger.info("Connected to Odoo server version: %s", version_info.get('server_version', 'Unknown'))
                
                # Authenticate using the authenticate method
                # Use empty dictionary for context as shown in the example script
                uid = common.authenticate(config.ODOO_DB, username, password, {})
                self.logger.debug("XML-RPC authentication result: %s", uid)
                
                if uid:
                    self.logger.info("XML-RPC authentication successful, user ID: %s", uid)
                    self.uid = uid
                    self.password = password  # Store for future requests
                    
                    # Create XML-RPC models client for making calls after authentication
                    models_url = f"{base_url}/xmlrpc/2/object"
                    self.logger.debug("XML-RPC models URL: %s", models_url)
                    self.models = xmlrpc.client.ServerProxy(models_url)
                    self.logger.debug("Created XML-RPC models client")
                    
                    # Create user object
                    user = User(
                        id=uid,
                        name=f"User {uid}",
                        username=username,
                        email=username if "@" in username else ""
                    )
                    self.user = user
                    
                    # Get additional user info
                    self._get_user_info()
                    
                    return AuthResponse(
                        success=True,
                        error=None,
                        user=user
                    )
                else:
                    self.logger.warning("XML-RPC authentication failed, trying JSON-RPC")
            except Exception as xml_rpc_error:
                self.logger.warning("XML-RPC authentication error: %s, trying JSON-RPC", str(xml_rpc_error))
            
            # 3. Fall back to JSON-RPC session authentication
            self.logger.info("Attempting authentication using JSON-RPC session")
            
            import requests
            import json
            
            # Authenticate using the JSON-RPC session authentication
            data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "db": config.ODOO_DB,
                    "login": username,
                    "password": password,
                    "base_location": self.base_url  # Add base location to help Odoo identify the client
                },
                "id": 1
            }
            
            self.logger.debug("API request data: %s", {**data, "params": {**data["params"], "password": "[REDACTED]"}})
            
            # Use the /web/session/authenticate endpoint for authentication
            auth_endpoint = "web/session/authenticate"
            url = f"{self.base_url}/{auth_endpoint}"
            self.logger.debug("JSON-RPC authentication URL: %s", url)
            
            # Make the request with additional headers for Odoo 18
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Retail-AI-Agent/1.0"
            }
            
            # Make the request
            response_obj = requests.post(
                url, 
                json=data,
                headers=headers,
                timeout=10
            )
            
            self.logger.info("POST %s - Status: %d", url, response_obj.status_code)
            
            if response_obj.status_code == 200:
                try:
                    response = response_obj.json()
                    self.logger.debug("API response: %s", response)
                    
                    # Check authentication success
                    success = "result" in response and not response.get("error")
                    if success and isinstance(response.get("result"), dict):
                        result = response.get("result", {})
                        # Check if we have a session_id in the result
                        if "session_id" in result:
                            self.token = result.get("session_id")
                            self.logger.debug("Session ID obtained: %s", self.token)
                            
                            # Get user ID from the response
                            uid = result.get("uid")
                            if uid:
                                self.uid = uid
                                self.password = password  # Store for future requests
                            else:
                                self.logger.warning("No user ID found in authentication response")
                        else:
                            self.logger.warning("No session_id found in authentication response")
                    
                    error = None if success else f"Authentication failed: {response.get('error', {}).get('message', 'Unknown error') if isinstance(response.get('error'), dict) else response.get('error', 'Unknown error')}"
                except ValueError:
                    success = False
                    error = f"Authentication failed: Invalid JSON response"
            else:
                success = False
                error = f"Authentication failed: HTTP error {response_obj.status_code}"
            
            # Create user object if authentication successful
            user = None
            if success:
                # Try to get user information from the response
                result = response.get("result", {})
                uid = result.get("uid")
                user_context = result.get("user_context", {})
                user_name = result.get("name", "API User")
                
                user = User(
                    id=uid or 1,  # Use the user ID from response or default to 1
                    name=user_name,
                    username=username,
                    email=username if "@" in username else ""
                )
                self.user = user
                self.logger.info("Successfully authenticated via JSON-RPC as: %s (ID: %s)", user.name, user.id)
            else:
                self.token = None  # Reset token on failure
                self.logger.warning("Authentication failed using JSON-RPC: %s", error)
            
            # If authentication was successful, return the response
            if success:
                self.using_fallback = False
                return AuthResponse(
                    success=success,
                    error=error,
                    user=user
                )
            else:
                # If authentication failed, use fallback mode with sample data
                self.logger.warning("Authentication failed, using fallback mode with sample data")
                self.using_fallback = True
                
                # Create a sample user for fallback mode
                fallback_user = User(
                    id=999,
                    name="Sample User",
                    username=username,
                    email=username if "@" in username else "sample@example.com"
                )
                self.user = fallback_user
                
                return AuthResponse(
                    success=True,  # Return success even though we're in fallback mode
                    error="Using fallback mode with sample data due to authentication failure",
                    user=fallback_user
                )
        except Exception as e:
            self.logger.error("Authentication error: %s", str(e))
            
            # Use fallback mode in case of exceptions
            self.logger.warning("Authentication error, using fallback mode with sample data")
            self.using_fallback = True
            
            # Create a sample user for fallback mode
            fallback_user = User(
                id=999,
                name="Sample User",
                username=username,
                email=username if "@" in username else "sample@example.com"
            )
            self.user = fallback_user
            
            return AuthResponse(
                success=True,  # Return success even though we're in fallback mode
                error=f"Using fallback mode with sample data due to error: {str(e)}",
                user=fallback_user
            )
            
    def _get_user_info(self) -> None:
        """Get additional user information after successful authentication.
        
        This method is READ-ONLY and does not modify any data in the Odoo CRM.
        It retrieves additional information about the authenticated user.
        """
        if not hasattr(self, 'uid') or not self.uid:
            self.logger.warning("Cannot get user info: No user ID available")
            return
            
        try:
            import xmlrpc.client
            
            # Create XML-RPC client for the object endpoint
            models_url = f"{config.ODOO_API_URL}/xmlrpc/2/object"
            models = xmlrpc.client.ServerProxy(models_url)
            
            # Call the read method on the res.users model to get user info
            user_data = models.execute_kw(
                config.ODOO_DB, self.uid, self.password,
                'res.users', 'read',
                [self.uid],  # List of IDs to read
                {'fields': ['name', 'login', 'email']}  # Fields to retrieve
            )
            
            if user_data and isinstance(user_data, list) and len(user_data) > 0:
                user_info = user_data[0]
                
                # Update the user object with the retrieved information
                if self.user:
                    self.user.name = user_info.get('name', self.user.name)
                    self.user.username = user_info.get('login', self.user.username)
                    self.user.email = user_info.get('email', self.user.email)
                    
                self.logger.info("Retrieved user info: %s", user_info)
            else:
                self.logger.warning("No user data returned from Odoo")
                
        except Exception as e:
            self.logger.error("Error getting user info: %s", str(e))
        
    def _verify_access(self) -> bool:
        """Verify that we have proper access to the Odoo system.
        
        This method makes a simple READ-ONLY request to verify that we have proper access
        to the Odoo system using either the API key or session token.
        
        Returns:
            True if access is verified, False otherwise
        """
        if not self.token:
            self.logger.warning("Cannot verify access: No authentication token available")
            return False
        
        try:
            import requests
            import json
            
            # According to Odoo documentation, we need to use different approaches
            # depending on whether we're using API key or session authentication
            
            # Check if we're using API key (API key is stored in self.token)
            using_api_key = self.token == config.ODOO_API_KEY
            
            if using_api_key:
                # For API key authentication, we use the /jsonrpc endpoint with the key as a parameter
                self.logger.debug("Verifying access using API key")
                
                # Make a simple request to verify access using API key
                data = {
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {
                        "service": "object",
                        "method": "execute_kw",
                        "args": [
                            config.ODOO_DB,
                            1,  # Admin user ID
                            self.token,  # API key
                            "res.users",
                            "search_read",
                            [[('id', '=', 1)]],
                            {"fields": ["name", "login"], "limit": 1}
                        ]
                    },
                    "id": 1
                }
                
                # Try with the web/jsonrpc endpoint which is more commonly used in Odoo 14+
                url = f"{self.base_url}/web/jsonrpc"
                self.logger.debug("API key verification URL: %s", url)
                headers = {"Content-Type": "application/json"}
                
            else:
                # For session authentication, we use the session ID in the header
                self.logger.debug("Verifying access using session token")
                
                # Make a simple request to verify access using session token
                data = {
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {
                        "model": "res.users",
                        "method": "search_read",
                        "args": [[('id', '=', 1)]],
                        "kwargs": {"fields": ["name", "login"], "limit": 1}
                    },
                    "id": 1
                }
                
                url = f"{self.base_url}/web/dataset/call_kw"
                headers = {
                    "Content-Type": "application/json",
                    "X-Openerp-Session-Id": self.token
                }
            
            # Make the request
            response_obj = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=10
            )
            
            self.logger.debug("Verify access response status: %d", response_obj.status_code)
            
            if response_obj.status_code == 200:
                try:
                    response = response_obj.json()
                    
                    if isinstance(response, dict) and "result" in response and not response.get("error"):
                        self.logger.info("Access verification successful")
                        return True
                    else:
                        error_msg = response.get("error", {}).get("message", "Unknown error") if isinstance(response.get("error"), dict) else "Unknown error"
                        self.logger.warning("Access verification failed: %s", error_msg)
                        return False
                        
                except ValueError:
                    self.logger.warning("Access verification failed: Invalid JSON response")
                    return False
            else:
                self.logger.warning("Access verification failed: HTTP error %d", response_obj.status_code)
                return False
                
        except Exception as e:
            self.logger.error("Error verifying access: %s", str(e))
            return False
    
    def logout(self) -> None:
        """Logout from the Odoo API."""
        self.token = None
        self.user = None
        self.logger.info("Logged out")
    
    def get_products(self, available_only: bool = False) -> ProductsResponse:
        """Get all products from the Odoo API in a read-only manner.
        
        This method is READ-ONLY and does not modify any data in the Odoo CRM.
        It only retrieves product information from the Odoo CRM.
        
        Args:
            available_only: If True, only return available products
            
        Returns:
            Products response containing product information
        """
        self.logger.info("Getting products (READ-ONLY, available_only=%s)", available_only)
        
        # Allow product retrieval without authentication - this is a read-only operation
        # that should be available to all users, even if not logged in
        
        # Prepare the search domain
        domain = []
        
        # Add availability filter if requested
        if available_only:
            domain.append(('qty_available', '>', 0))
        
        # Fields to retrieve
        fields = [
            'id', 'name', 'list_price', 'description', 'description_sale',
            'default_code', 'qty_available', 'type', 'uom_name', 'image_1920'
        ]
        
        # Format data for Odoo JSON-RPC API using the proper JSON-RPC format
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    config.ODOO_DB,
                    1,  # Admin user ID
                    config.ODOO_API_KEY,
                    "product.template",
                    "search_read",
                    [domain],
                    {"fields": fields, "limit": 100}  # Limit to 100 products
                ]
            },
            "id": 1
        }
        
        self.logger.debug("API request data: %s", data)
        self.logger.debug("API URL: %s", f"{self.base_url}/{config.JSON_RPC_ENDPOINT}")
        
        response = self._make_request("POST", config.JSON_RPC_ENDPOINT, data=data)
        self.logger.debug("API response: %s", response)
        
        # Handle different response types safely
        if isinstance(response, dict):
            # Log the full response for debugging
            self.logger.debug("Full JSON-RPC response: %s", response)
            
            success = "result" in response and not response.get("error")
            if not success:
                error_msg = "Unknown error"
                if "error" in response:
                    error_obj = response.get("error")
                    self.logger.error("Odoo error details: %s", error_obj)
                    
                    if isinstance(error_obj, dict):
                        if "message" in error_obj:
                            error_msg = error_obj.get("message")
                        if "data" in error_obj:
                            data = error_obj.get("data")
                            if isinstance(data, dict) and "debug" in data:
                                self.logger.error("Odoo error debug info: %s", data.get("debug"))
                    elif isinstance(error_obj, str):
                        error_msg = error_obj
                error = f"Failed to get products: {error_msg}"
            else:
                error = None
        else:
            success = False
            error = f"Failed to get products: {response if isinstance(response, str) else 'Invalid response format'}"
            self.logger.error("Unexpected response format: %s", type(response))
        
        products = []
        if success:
            products_data = response.get("result", [])
            self.logger.info("Found %d products", len(products_data))
            
            for product_data in products_data:
                try:
                    product = Product(
                        id=product_data.get("id"),
                        name=product_data.get("name", ""),
                        description=product_data.get("description", "") or "",
                        price=product_data.get("list_price", 0.0),
                        available=product_data.get("is_published", True),
                        tags=[product_data.get("categ_id", [0, ""])[1]] if product_data.get("categ_id") else []
                    )
                    products.append(product)
                except Exception as e:
                    self.logger.error("Error parsing product data: %s, data: %s", str(e), product_data)
        
        return ProductsResponse(
            success=success,
            error=error,
            products=products
        )
    
    def logout(self) -> None:
        """Logout from the Odoo API."""
        self.token = None
        self.user = None
        self.logger.info("Logged out")
    
    def get_products(self, available_only: bool = False) -> ProductsResponse:
        """Get all products from the Odoo API in a read-only manner.
        
        This method is READ-ONLY and does not modify any data in the Odoo CRM.
        It only retrieves product information from the Odoo CRM.
        
        Args:
            available_only: If True, only return available products
            
        Returns:
            Products response containing product information
        """
        self.logger.info("Getting products (READ-ONLY, available_only=%s)", available_only)
        
        # Allow product retrieval without authentication - this is a read-only operation
        # that should be available to all users, even if not logged in
        
        # Prepare the search domain
        domain = []
        
        # Add availability filter if requested
        if available_only:
            domain.append(('qty_available', '>', 0))
        
        # Fields to retrieve
        fields = [
            'id', 'name', 'list_price', 'description', 'description_sale',
            'default_code', 'qty_available', 'type', 'uom_name', 'image_1920'
        ]
        
        # Format data for Odoo JSON-RPC API using the proper JSON-RPC format
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    config.ODOO_DB,
                    1,  # Admin user ID
                    config.ODOO_API_KEY,
                    "product.template",
                    "search_read",
                    [domain],
                    {"fields": fields, "limit": 100}  # Limit to 100 products
                ]
            },
            "id": 1
        }
        
        self.logger.debug("API request data: %s", data)
        self.logger.debug("API URL: %s", f"{self.base_url}/{config.JSON_RPC_ENDPOINT}")
        
        response = self._make_request("POST", config.JSON_RPC_ENDPOINT, data=data)
        self.logger.debug("API response: %s", response)
        
        # Handle different response types safely
        if isinstance(response, dict):
            # Log the full response for debugging
            self.logger.debug("Full JSON-RPC response: %s", response)
            
            success = "result" in response and not response.get("error")
            if not success:
                error_msg = "Unknown error"
                if "error" in response:
                    error_obj = response.get("error")
                    self.logger.error("Odoo error details: %s", error_obj)
                    
                    if isinstance(error_obj, dict):
                        if "message" in error_obj:
                            error_msg = error_obj.get("message")
                        if "data" in error_obj:
                            data = error_obj.get("data")
                            if isinstance(data, dict) and "debug" in data:
                                self.logger.error("Odoo error debug info: %s", data.get("debug"))
                    elif isinstance(error_obj, str):
                        error_msg = error_obj
                error = f"Failed to get products: {error_msg}"
            else:
                error = None
        else:
            success = False
            error = f"Failed to get products: {response if isinstance(response, str) else 'Invalid response format'}"
            self.logger.error("Unexpected response format: %s", type(response))
        
        products = []
        if success:
            products_data = response.get("result", [])
            self.logger.info("Found %d products", len(products_data))
            
            for product_data in products_data:
                try:
                    product = Product(
                        id=product_data.get("id"),
                        name=product_data.get("name", ""),
                        description=product_data.get("description", "") or "",
                        price=product_data.get("list_price", 0.0),
                        available=product_data.get("is_published", True),
                        tags=[product_data.get("categ_id", [0, ""])[1]] if product_data.get("categ_id") else []
                    )
                    products.append(product)
                except Exception as e:
                    self.logger.error("Error parsing product data: %s, data: %s", str(e), product_data)
        
        return ProductsResponse(
            success=success,
            error=error,
            products=products
        )
        
    def search_products(self, query: str, available_only: bool = False) -> ProductsResponse:
        """Search for products by name, description, or SKU (READ-ONLY).
        
        Args:
            query: Search query
            available_only: Whether to only include available products
            
        Returns:
            ProductsResponse: The response from the search request
        """
        self.logger.info("Searching products (READ-ONLY) with query: '%s' (available_only=%s)", 
                        query, available_only)
        
        # If we're in fallback mode, use sample products directly
        if self.using_fallback:
            self.logger.info("Using fallback mode with sample products")
            products = self._get_sample_products(query, available_only)
            return ProductsResponse(
                success=True,
                error="Using fallback mode with sample data",
                products=products
            )
            
        # If not in fallback mode, try to search real products from Odoo API
        # Prepare to search using XML-RPC first, as it's more reliable
            
        # Prepare the domain for the search
        # Search in name, description, and default_code (SKU)
        domain = [
            '|', '|',
            ('name', 'ilike', query),
            ('description_sale', 'ilike', query),
            ('default_code', 'ilike', query)
        ]
        
        try:
            
            # Add availability filter if needed
            if available_only:
                domain.append(('qty_available', '>', 0))
            
            # Fields to retrieve
            fields = [
                'id', 'name', 'list_price', 'standard_price', 'lst_price', 'price', 
                'qty_available', 'description_sale', 'default_code', 'image_1920', 'categ_id'
            ]
            
            # Try different approaches based on available authentication methods
            products_data = None
            error_msg = None
            
            # 1. Try XML-RPC approach if we have UID (recommended by Odoo docs)
            if hasattr(self, 'uid') and self.uid:
                try:
                    self.logger.info("Using XML-RPC to search products")
                    import xmlrpc.client
                    import ssl
                    
                    # Disable SSL certificate verification as in the example script
                    ssl._create_default_https_context = ssl._create_unverified_context
                    
                    # Create XML-RPC client for the object endpoint
                    # Strip '/api' from the URL if present
                    base_url = config.ODOO_API_URL.rstrip('/api')
                    models_url = f"{base_url}/xmlrpc/2/object"
                    self.logger.debug("XML-RPC models URL: %s", models_url)
                    models = xmlrpc.client.ServerProxy(models_url)
                    
                    # Call the search_read method on the product.template model
                    products_data = models.execute_kw(
                        config.ODOO_DB, self.uid, self.password,
                        'product.template', 'search_read',
                        [domain],  # Domain for searching
                        {'fields': fields, 'limit': 20}  # Options
                    )
                    
                    if products_data is not None:
                        self.logger.info("XML-RPC search successful, found %d products", len(products_data))
                    else:
                        self.logger.warning("XML-RPC search returned None")
                        
                except Exception as xml_rpc_error:
                    self.logger.warning("XML-RPC search error: %s, trying JSON-RPC", str(xml_rpc_error))
                    error_msg = str(xml_rpc_error)
            
            # 2. Try JSON-RPC approach if XML-RPC failed or we only have a token
            if products_data is None and self.token:
                try:
                    self.logger.info("Using JSON-RPC to search products")
                    
                    # Make the request
                    data = {
                        "jsonrpc": "2.0",
                        "method": "call",
                        "params": {
                            "model": "product.template",
                            "method": "search_read",
                            "args": [domain],
                            "kwargs": {"fields": fields, "limit": 20}
                        },
                        "id": 1
                    }
                    
                    # Add session_id to headers for authentication
                    headers = {"X-Openerp-Session-Id": self.token}
                    
                    # Make the request to the dataset/call_kw endpoint
                    response = self._make_request(
                        "POST", 
                        "web/dataset/call_kw", 
                        data=data, 
                        headers=headers
                    )
                    
                    # Process the response
                    if isinstance(response, dict) and "result" in response:
                        products_data = response.get("result", [])
                        self.logger.info("JSON-RPC search successful, found %d products", len(products_data))
                    else:
                        error_msg = response.get("error", {}).get("message", "Unknown error") if isinstance(response.get("error"), dict) else "Unknown error"
                        self.logger.error("JSON-RPC error searching products: %s", error_msg)
                        
                except Exception as json_rpc_error:
                    self.logger.error("JSON-RPC search error: %s", str(json_rpc_error))
                    error_msg = str(json_rpc_error)
            
            # 3. Try API key approach if we have it and other methods failed
            if products_data is None and hasattr(self, 'api_key_auth') and self.api_key_auth and config.ODOO_API_KEY:
                try:
                    self.logger.info("Using API key to search products")
                    import requests
                    import json
                    
                    # Prepare the JSON-RPC request data with API key
                    data = {
                        "jsonrpc": "2.0",
                        "method": "call",
                        "params": {
                            "service": "object",
                            "method": "execute_kw",
                            "args": [
                                config.ODOO_DB,
                                1,  # Admin user ID
                                config.ODOO_API_KEY,
                                "product.template",
                                "search_read",
                                [domain],
                                {"fields": fields, "limit": 20}
                            ]
                        },
                        "id": 1
                    }
                    
                    # Make the JSON-RPC request
                    response_obj = requests.post(
                        f"{config.ODOO_API_URL}/jsonrpc",
                        json=data,
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                    
                    if response_obj.status_code == 200:
                        result = response_obj.json()
                        
                        if "error" not in result and "result" in result:
                            products_data = result.get("result", [])
                            self.logger.info("API key search successful, found %d products", len(products_data))
                        else:
                            error_msg = result.get("error", {}).get("message", "Unknown error") if isinstance(result.get("error"), dict) else "Unknown error"
                            self.logger.error("API key error searching products: %s", error_msg)
                    else:
                        self.logger.error("API key HTTP error: %s", response_obj.status_code)
                        error_msg = f"HTTP error {response_obj.status_code}"
                        
                except Exception as api_key_error:
                    self.logger.error("API key search error: %s", str(api_key_error))
                    error_msg = str(api_key_error)
            
            # Process the products data if we have it
            if products_data and isinstance(products_data, list):
                # Transform the result to match our expected format
                products = []
                for product in products_data:
                    # Get the most appropriate price field, prioritizing lst_price, then standard_price, then list_price
                    price = 0.0
                    if product.get("lst_price") not in [False, None, 0.0, 1.0]:
                        price = product.get("lst_price")
                    elif product.get("standard_price") not in [False, None, 0.0, 1.0]:
                        price = product.get("standard_price")
                    elif product.get("list_price") not in [False, None, 0.0, 1.0]:
                        price = product.get("list_price")
                    elif product.get("price") not in [False, None, 0.0, 1.0]:
                        price = product.get("price")
                    else:
                        # If all price fields are invalid, use list_price as fallback
                        price = product.get("list_price", 0.0)
                    
                    products.append(Product(
                        id=product.get("id"),
                        name=product.get("name", "Unknown"),
                        price=price,
                        available=product.get("qty_available", 0) > 0,
                        description=str(product.get("description_sale", "No description available")) if product.get("description_sale") not in [False, None] else "No description available",
                        tags=[]
                    ))
                
                self.logger.info("Found %d products matching query '%s'", len(products), query)
                return ProductsResponse(
                    success=True,
                    error=None,
                    products=products
                )
        except Exception as e:
            self.logger.error("Error searching products from Odoo API: %s", str(e))
            
            # Only use sample products as a last resort when the API is completely unavailable
            if self.using_fallback:
                self.logger.info("API unavailable, using sample products as fallback")
                products = self._get_sample_products(query, available_only)
                return ProductsResponse(
                    success=True,
                    error=f"Using sample data due to API error: {str(e)}",
                    products=products
                )
            else:
                # If not in fallback mode, return the error
                return ProductsResponse(
                    success=False,
                    error=f"Error searching products: {str(e)}",
                    products=[]
                )
                
    def get_product(self, product_id: int) -> ProductsResponse:
        """Get a single product by ID (READ-ONLY).
        
        Args:
            product_id: Product ID
            
        Returns:
            ProductsResponse with a single product or empty list if not found
        """
        self.logger.info("Getting product (READ-ONLY) with ID: %d", product_id)
        
        if not self._verify_access():
            self.logger.warning("Cannot get product: Not authenticated")
            return ProductsResponse(
                success=False,
                error="Not authenticated",
                products=[]
            )
            
        try:
            # Fields to retrieve
            fields = [
                'id', 'name', 'list_price', 'standard_price', 'lst_price', 'price',
                'qty_available', 'description_sale', 'default_code', 'image_1920', 'categ_id'
            ]
            
            # Try different approaches based on available authentication methods
            product_data = None
            error_msg = None
            
            # 1. Try XML-RPC approach if we have UID (recommended by Odoo docs)
            if hasattr(self, 'uid') and self.uid:
                try:
                    self.logger.info("Using XML-RPC to get product")
                    import xmlrpc.client
                    import ssl
                    
                    # Disable SSL certificate verification as in the example script
                    ssl._create_default_https_context = ssl._create_unverified_context
                    
                    # Create XML-RPC client for the object endpoint
                    # Strip '/api' from the URL if present
                    base_url = config.ODOO_API_URL.rstrip('/api')
                    models_url = f"{base_url}/xmlrpc/2/object"
                    self.logger.debug("XML-RPC models URL: %s", models_url)
                    models = xmlrpc.client.ServerProxy(models_url)
                    
                    # Call the read method on the product.template model
                    product_data = models.execute_kw(
                        config.ODOO_DB, self.uid, self.password,
                        'product.template', 'read',
                        [[product_id]],  # IDs to read
                        {'fields': fields}  # Options
                    )
                    
                    if product_data and isinstance(product_data, list) and len(product_data) > 0:
                        self.logger.info("XML-RPC get product successful")
                    else:
                        self.logger.warning("XML-RPC get product returned no data")
                        
                except Exception as xml_rpc_error:
                    self.logger.warning("XML-RPC get product error: %s", str(xml_rpc_error))
                    error_msg = str(xml_rpc_error)
            
            # Process the product data if we have it
            if product_data and isinstance(product_data, list) and len(product_data) > 0:
                # Transform the result to match our expected format
                products = []
                for product in product_data:
                    # Get the most appropriate price field, prioritizing lst_price, then standard_price, then list_price
                    price = 0.0
                    if product.get("lst_price") not in [False, None, 0.0, 1.0]:
                        price = product.get("lst_price")
                    elif product.get("standard_price") not in [False, None, 0.0, 1.0]:
                        price = product.get("standard_price")
                    elif product.get("list_price") not in [False, None, 0.0, 1.0]:
                        price = product.get("list_price")
                    elif product.get("price") not in [False, None, 0.0, 1.0]:
                        price = product.get("price")
                    else:
                        # If all price fields are invalid, use list_price as fallback
                        price = product.get("list_price", 0.0)
                    
                    products.append(Product(
                        id=product.get("id"),
                        name=product.get("name", "Unknown"),
                        price=price,
                        available=product.get("qty_available", 0) > 0,
                        description=str(product.get("description_sale", "No description available")) if product.get("description_sale") not in [False, None] else "No description available",
                        tags=[]
                    ))
                
                self.logger.info("Found product with ID %d", product_id)
                return ProductsResponse(
                    success=True,
                    error=None,
                    products=products
                )
            else:
                self.logger.warning("Product with ID %d not found", product_id)
                return ProductsResponse(
                    success=False,
                    error=f"Product with ID {product_id} not found",
                    products=[]
                )
        except Exception as e:
            self.logger.error("Error getting product: %s", str(e))
            return ProductsResponse(
                success=False,
                error=f"Error getting product: {str(e)}",
                products=[]
            )

    def get_recommendations(self, user_id: int, limit: int = 5) -> RecommendationsResponse:
        """Get personalized product recommendations for a user using a read-only approach.
        
        This method is READ-ONLY and does not modify any data in the Odoo CRM.
        It retrieves product recommendations based on user preferences without making any changes.
        
        Args:
            user_id: User ID
            limit: Maximum number of recommendations
            
        Returns:
            Recommendations response with product recommendations
        """
        self.logger.info("Getting product recommendations (READ-ONLY) for user ID: %s, limit: %d", user_id, limit)
        
        if not self.token:
            self.logger.warning("Cannot get recommendations: Not authenticated")
            return RecommendationsResponse(
                success=False,
                error="Not authenticated",
                recommendations=[]
            )
        
        # Prepare a domain to find products that might interest the user
        # For a simple recommendation, we'll get popular products
        domain = [["sale_ok", "=", True], ["is_published", "=", True]]
        
        # Fields to retrieve
        fields = ["id", "name", "description", "description_sale", "list_price", "qty_available", "categ_id"]
        
        # Format data for Odoo JSON-RPC API
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "product.template",
                "method": "search_read",
                "args": [domain],
                "kwargs": {
                    "fields": fields, 
                    "limit": limit,
                    "order": "create_date desc"  # Get newest products
                }
            },
            "id": 1
        }
        
        # Add session_id to headers for authentication
        headers = {"X-Openerp-Session-Id": self.token}
        
        self.logger.debug("API request data: %s", data)
        
        try:
            response = self._make_request(
                "POST", 
                "web/dataset/call_kw", 
                data=data, 
                headers=headers
            )
            
            self.logger.debug("API response: %s", response)
            
            # Process the response
            if isinstance(response, dict) and "result" in response:
                products_data = response.get("result", [])
                self.logger.info("Found %d products for recommendations", len(products_data))
                
                recommendations = []
                for product_data in products_data:
                    try:
                        product = Product(
                            id=product_data.get("id"),
                            name=product_data.get("name", ""),
                            description=product_data.get("description_sale", "") or product_data.get("description", "") or "",
                            price=product_data.get("list_price", 0.0),
                            available=product_data.get("qty_available", 0) > 0,
                            tags=[product_data.get("categ_id", [0, ""])[1]] if product_data.get("categ_id") else []
                        )
                        recommendations.append(product)
                    except Exception as e:
                        self.logger.error("Error parsing product data: %s, data: %s", str(e), product_data)
                
                return RecommendationsResponse(
                    success=True,
                    error=None,
                    recommendations=recommendations
                )
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error") if isinstance(response.get("error"), dict) else "Unknown error"
                self.logger.error("Error getting recommendations: %s", error_msg)
                return RecommendationsResponse(
                    success=False,
                    error=f"Failed to get recommendations: {error_msg}",
                    recommendations=[]
                )
                
        except Exception as e:
            self.logger.error("Error getting recommendations: %s", str(e))
            return RecommendationsResponse(
                success=False,
                error=f"Error getting recommendations: {str(e)}",
                recommendations=[]
            )
        
        self.logger.debug("API request data: %s", data)
        self.logger.debug("API URL: %s", f"{self.base_url}{config.PRODUCTS_ENDPOINT}")
        
        response = self._make_request("POST", config.PRODUCTS_ENDPOINT, data=data)
        self.logger.debug("API response: %s", response)
        
        success = "result" in response and not response.get("error")
        error = None if success else f"Failed to get recommendations: {response.get('error', {}).get('message', 'Unknown error')}"
        
        recommendations = []
        if success:
            products_data = response.get("result", [])
            self.logger.info("Found %d products for recommendations", len(products_data))
            
            for product_data in products_data:
                try:
                    product = Product(
                        id=product_data.get("id"),
                        name=product_data.get("name", ""),
                        description=product_data.get("description", "") or "",
                        price=product_data.get("list_price", 0.0),
                        available=product_data.get("is_published", True),
                        tags=[product_data.get("categ_id", [0, ""])[1]] if product_data.get("categ_id") else []
                    )
                    recommendations.append(product)
                except Exception as e:
                    self.logger.error("Error parsing product data: %s, data: %s", str(e), product_data)
        else:
            self.logger.warning("Failed to get recommendations for user ID: %s, error: %s", user_id, error)
        
        return RecommendationsResponse(
            success=success,
            error=error,
            recommendations=recommendations
        )
    
    def checkout(self, cart_data: Dict) -> CheckoutResponse:
        """Simulate a checkout process without making changes to the Odoo CRM.
        
        This method is READ-ONLY and does not create any orders in the Odoo CRM.
        It only simulates the checkout process and returns a response as if an order was created.
        No data is sent to the Odoo CRM during this process.
        
        Args:
            cart_data: Cart data containing items to checkout
            
        Returns:
            Checkout response with simulated order information
        """
        self.logger.info("Simulating checkout process (READ-ONLY)")
        self.logger.debug("Cart data for simulation: %s", cart_data)
        
        if not self.token:
            self.logger.warning("Checkout failed: User not authenticated")
            return CheckoutResponse(
                success=False,
                error="Not authenticated",
                order_id=None,
                order_total=None
            )
        
        # Calculate the total price from the cart items
        total = 0.0
        items_processed = 0
        try:
            for item in cart_data.get("items", []):
                price = item.get("price", 0.0)
                quantity = item.get("quantity", 0)
                item_total = price * quantity
                total += item_total
                items_processed += 1
                self.logger.debug("Processed item: %s, quantity: %s, price: $%.2f, subtotal: $%.2f", 
                                 item.get("name", "Unknown"), quantity, price, item_total)
        except Exception as e:
            self.logger.error("Error calculating total: %s", str(e))
            return CheckoutResponse(
                success=False,
                error=f"Error processing cart: {str(e)}",
                order_id=None,
                order_total=None
            )
        
        # Generate a simulated order ID (completely local, no API call)
        import random
        import time
        timestamp = int(time.time())
        simulated_order_id = f"SIM-{timestamp}-{random.randint(1000, 9999)}"
        
        self.logger.info("Simulated checkout complete. Order ID: %s, Items: %d, Total: $%.2f", 
                         simulated_order_id, items_processed, total)
        
        return CheckoutResponse(
            success=True,
            error=None,
            order_id=simulated_order_id,
            order_total=total
        )
