#!/bin/bash

curl -X DELETE -k https://localhost:5000/messages/fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9 & PIDDBH1=$!
curl -X DELETE -k https://localhost:5000/messages/2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae & PIDDFH1=$!
curl -k https://localhost:5000/messages/fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9 & PIDBH1=$!
curl -k https://localhost:5000/messages/2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae & PIDFH1=$!
curl -k https://localhost:5000/messages -X POST -d '{"message": "foo"}' & PIDFOO1=$!
curl -k https://localhost:5000/messages -X POST -d '{"message": "foo"}' & PIDFOO2=$!
curl -k https://localhost:5000/messages/fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9 & PIDBH2=$!
curl -k https://localhost:5000/messages/fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9 & PIDBH3=$!
curl -k https://localhost:5000/messages/2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae & PIDFH2=$!
curl -k https://localhost:5000/messages -X POST -d '{"message": "bar"}' & PIDBAR1=$!
curl -k https://localhost:5000/messages -X POST -d '{"message": "bar"}' & PIDBAR2=$!
curl -k https://localhost:5000/messages/fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9 & PIDBH4=$!
curl -k https://localhost:5000/messages/2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae & PIDFH3=$!
curl -k https://localhost:5000/messages/fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9 & PIDBH5=$!
curl -k https://localhost:5000/messages/2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae & PIDFH3=$!
wait $PIDFOO1
wait $PIDFOO2
wait $PIDBAR1
wait $PIDBAR2
wait $PIDDBH1
wait $PIDBH1
wait $PIDBH2
wait $PIDBH3
wait $PIDBH4
wait $PIDBH5
wait $PIDDFH1
wait $PIDFH1
wait $PIDFH2
wait $PIDFH3
