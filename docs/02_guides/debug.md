# Debug Guide

## Logs

```bash
docker logs xianyuautoagent
```

## Common Issues

### WebSocket connection drops
→ Check `COOKIES_STR` is not expired
→ Verify network connection

### Token refresh fails
→ Check Cookie is valid
→ Verify device ID is correct

### Cannot fetch product info
→ Check API call frequency
→ Confirm product ID is valid

### Message decryption fails
→ Check encryption algorithm implementation
→ Verify decryption key is correct
