import argparse
import requests
import json
import logging

# Configure logging
logging.basicConfig(filename='check_balance.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

LIMIT = 120
SATOSHI = 1e8

def check_balance(input_file, output_file):
  """Checks balance of multiple Bitcoin addresses and saves to a file.

  Args:
      input_file (str): Path to the text file containing addresses (one per line).
      output_file (str): Path to the output text file for results.
  """

  with open(input_file, 'r') as f1, open(output_file, 'w') as f2:
    addresses = [line.strip() for line in f1]
    logging.info(f'Loaded {len(addresses)} addresses from {input_file}')

    max_address_len = max(len(address) for address in addresses)  # Find longest address
    balances_with_addresses = []  # List to store addresses with positive balances

    for i in range(0, len(addresses), LIMIT):
      batch = addresses[i:i+LIMIT]
      url = f"https://blockchain.info/multiaddr?active={','.join(batch)}&format=json"

      try:
        response = requests.get(url, timeout=15) #timing management, timeout=15 is ideal
        response.raise_for_status()  # Raise exception for non-2xx status codes

        data = response.json()
        # Check if data['addresses'] is a list or a dictionary
        if isinstance(data['addresses'], list):
          logging.warning("API response structure changed: 'addresses' is a list")
          for inner_address in data['addresses']:
              try:
                  # Assuming elements in the list are dictionaries with address info
                  address = inner_address.get('address')
                  balance = inner_address.get('final_balance', 0) / SATOSHI
                  if balance > 0:  # Check for positive balance
                      balances_with_addresses.append((address, balance))
              except Exception as e:
                  logging.error(f"Error processing address {inner_address}: {e}")
        else:
          for inner_address, info in data['addresses'].items():
              try:
                  balance = info.get('final_balance', 0) / SATOSHI
                  if balance > 0:  # Check for positive balance
                      balances_with_addresses.append((inner_address, balance))
              except Exception as e:
                  logging.error(f"Error processing address {inner_address}: {e}")

      except requests.exceptions.RequestException as e:
        logging.error(f"Error processing batch: {e}")
        # Implement retry logic or handle failure (e.g., logging)

    # Write addresses with positive balance first
    for address, balance in balances_with_addresses:
        f2.write(f"{address:{max_address_len}}  {balance:.8f}\n")

    # Then write addresses with zero balance (if any)
    for address in addresses:
        if address not in [a for a, _ in balances_with_addresses]:
            f2.write(f"{address:{max_address_len}}  0.00000000\n")

  logging.info(f'Balance results saved to {output_file}')
  print(f"Balance results saved to {output_file}")

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("input_file", help="Text file containing Bitcoin addresses")
  parser.add_argument("output_file", help="Output file for balance information")
  args = parser.parse_args()
  check_balance(args.input_file, args.output_file)
  

# run the code like this check_balance.py input.txt output.txt
