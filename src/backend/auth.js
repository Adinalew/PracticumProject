const express = require('express');
const router = express.Router();

// Mock database
const users = [];

// Login endpoint
router.post('/login', (req, res) => {
    const { email, password } = req.body;
    const user = users.find(u => u.email === email && u.password === password);
    if (user) {
        res.status(200).send({ message: 'Login successful' });
    } else {
        res.status(401).send({ message: 'Invalid credentials' });
    }
});

// Register endpoint
router.post('/register', (req, res) => {
    const { email, password } = req.body;
    if (users.find(u => u.email === email)) {
        res.status(400).send({ message: 'User already exists' });
    } else {
        users.push({ email, password });
        res.status(201).send({ message: 'Registration successful' });
    }
});

module.exports = router;
